#!/usr/bin/env python3
"""verify_replacements.py — Independently verify Gemini's 94 PMID replacements
against live PubMed before any DB write.

For each replacement (original_pmid -> gathered_pmid) we check, using NCBI eutils
only (no LLM tokens):
  1. gathered PMID is a REAL PubMed record (esummary returns a title)
  2. the gathered abstract actually contains BOTH entities + an action keyword
     (i.e. the proof sentence is real, not hallucinated)
  3. whether the ORIGINAL pmid's abstract even mentions both entities
     (if not, the replacement is clearly justified)

Output: data/REPLACEMENT_VERIFICATION.json with a per-edge verdict.
"""
import json, re, time, sys
import requests

EMAIL = "research@komposos.org"; TOOL = "KOMPOSOS-IV-PHARM"
ESUM = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

KW = {
 'inhibits':["inhib","antagon","block","suppress","downregulat","reduc","potency","ic50","deplet","silenc","knockdown"],
 'activates':["activat","agonist","induc","upregulat","stimulat","potentiat","promot","trigger"],
 'associated_with':["associat","linked","implicat","correlat","overexpress","mutation","biomarker","marker","prognostic","pathway"],
 'treats':["treat","therap","clinical","effica","approv","indicat","respon","survival","patient"],
 'driver_of':["driver","drives","caus","induc","promot","oncogen","tumorigen","pathogenesis"],
 'binds':["bind","affinity","complex","engage","dock","partner","interact","kd","ki"],
 'interacts':["interact","bind","complex","partner","physical","dock"],
 'phosphorylates':["phosphorylat","kinase"],
 'indirect_inhibitor':["inhib","block","suppress","downregulat","reduc","indirect","deplet"],
 'synergizes_with':["synerg","combin","potentiat","additive","enhanc"],
}

def _get(url, params, tries=4):
    for a in range(tries):
        try:
            return requests.get(url, params=params, timeout=45)
        except Exception as ex:
            if a==tries-1: raise
            time.sleep(1.5*(a+1))

def esummary(pmids):
    r = _get(ESUM, {'db':'pubmed','id':','.join(pmids),'retmode':'json','tool':TOOL,'email':EMAIL})
    return r.json().get('result', {})

def fetch_abstract(pmid):
    r = _get(EFETCH, {'db':'pubmed','id':pmid,'retmode':'xml','tool':TOOL,'email':EMAIL})
    secs = re.findall(r'<AbstractText[^>]*>(.*?)</AbstractText>', r.text, re.DOTALL)
    title = re.findall(r'<ArticleTitle[^>]*>(.*?)</ArticleTitle>', r.text, re.DOTALL)
    txt = " ".join(re.sub(r'<[^>]+>','',s) for s in (title+secs))
    return txt

def term_in(term, text):
    return re.search(r"\b"+re.escape(term)+r"s?\b", text, re.IGNORECASE) is not None

def kw_in(rel, text):
    for k in KW.get(rel, ["associat"]):
        if k.lower() in text.lower():
            return k
    return None

def main():
    g = json.load(open('data/GATHERED_PMID_LIST.json', encoding='utf-8'))
    t = json.load(open('data/TARGETED_SEARCH_RESULTS.json', encoding='utf-8'))
    broad = {x['edge_id']: x for x in t if x.get('status')=='PROPOSED_FIX_BROAD'}

    reps = []
    for e in g:
        eid=e['edge_id']; orig=str(e.get('original_pmid') or ''); st=e['status']
        if st in ('VERIFIED','PROPOSED_FIX'):
            new=str(e.get('gathered_pmid') or '')
            if new and new!=orig:
                reps.append({**e,'final_pmid':new,'tier':'gathered'})
        elif st=='NOT_FOUND' and eid in broad:
            b=broad[eid]; new=str(b.get('gathered_pmid') or '')
            if new and new!=orig:
                reps.append({'edge_id':eid,'source':e['source'],'relation':e['relation'],
                             'target':e['target'],'original_pmid':orig,'final_pmid':new,
                             'proof_sentence':b.get('proof_sentence',''),'tier':'broad'})
    print(f"Verifying {len(reps)} replacements against live PubMed...\n")

    # batch realness check on gathered + original
    all_ids = sorted({r['final_pmid'] for r in reps} | {r['original_pmid'] for r in reps if r['original_pmid']})
    real = {}
    for i in range(0, len(all_ids), 100):
        chunk = all_ids[i:i+100]
        d = esummary(chunk); time.sleep(0.35)
        for p in chunk:
            rec = d.get(p)
            real[p] = rec.get('title','') if rec and 'title' in rec else None

    results=[]
    for i, r in enumerate(reps):
        src=r['source']; tgt=r['target']; rel=r['relation']
        new=r['final_pmid']; orig=r['original_pmid']
        s_name=src.replace('_',' '); t_name=tgt.replace('_',' ')
        new_title = real.get(new)
        verdict={'edge_id':r['edge_id'],'relation':rel,'source':src,'target':tgt,
                 'original_pmid':orig,'final_pmid':new,'tier':r['tier'],
                 'new_pmid_real': new_title is not None,'new_title':(new_title or '')[:120]}
        if not new_title:
            verdict['status']='REJECT_FAKE_PMID'; results.append(verdict)
            print(f"[{i+1}/{len(reps)}] {r['edge_id']}: NEW PMID NOT REAL"); time.sleep(0.35); continue
        ab = fetch_abstract(new); time.sleep(0.35)
        has_src=term_in(s_name,ab); has_tgt=term_in(t_name,ab); kw=kw_in(rel,ab)
        verdict['new_has_both_entities']=bool(has_src and has_tgt)
        verdict['new_keyword']=kw
        # was original off-topic?
        orig_title = real.get(orig)
        verdict['orig_pmid_real']=orig_title is not None
        if orig and orig_title is not None:
            ab_o=fetch_abstract(orig); time.sleep(0.35)
            verdict['orig_has_both_entities']=bool(term_in(s_name,ab_o) and term_in(t_name,ab_o))
        else:
            verdict['orig_has_both_entities']=False
        # final judgement
        if has_src and has_tgt and kw:
            verdict['status']='REPLACE_OK'
        elif has_src and has_tgt:
            verdict['status']='REPLACE_WEAK_NO_KEYWORD'
        else:
            verdict['status']='REJECT_ENTITIES_MISSING'
        results.append(verdict)
        print(f"[{i+1}/{len(reps)}] {r['edge_id']}: {verdict['status']} "
              f"(both={verdict['new_has_both_entities']} kw={kw} orig_ontopic={verdict['orig_has_both_entities']})")

    json.dump(results, open('data/REPLACEMENT_VERIFICATION.json','w'), indent=2)
    from collections import Counter
    print("\n=== SUMMARY ===")
    for k,v in Counter(x['status'] for x in results).items():
        print(f"  {v:>3}  {k}")
    print("Wrote data/REPLACEMENT_VERIFICATION.json")

if __name__=='__main__':
    main()

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 James Ray Hawkins

import sqlite3

conn = sqlite3.connect('data/proteins/cancer_proteins.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(morphisms)')
print('Morphisms table columns:')
for row in cursor.fetchall():
    print(f'  {row[1]} ({row[2]})')
conn.close()

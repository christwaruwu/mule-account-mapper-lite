"""
Script untuk membersihkan dan memvalidasi data transaksi.
Langkah cleaning:
1. Hapus transaksi duplikat
2. Hapus transaksi yang gagal (status='failed')
3. Filter transaksi dengan amount <= 0
4. Standarisasi format tanggal
5. Hapus transaksi dari pengirim ke dirinya sendiri
6. Tambah kolom tambahan yang berguna untuk analisis
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_data(raw_dir='data/raw'):
    """Load data mentah dari file CSV"""
    users = pd.read_csv(os.path.join(raw_dir, 'users.csv'))
    transactions = pd.read_csv(os.path.join(raw_dir, 'transactions_raw.csv'))

    print(f"✅ Data loaded: ")
    print(f"Users: {len(users)} baris")
    print(f"Transactions: {len(transactions)} baris")

    return users, transactions

def clean_transactions(df):
    """
    Membersihkan data transaksi step by step.

    Parameter:
    - df: DataFrame transaksi mentah

    Return:
    - DataFrame transaksi yang sudah bersih
    """
    print("\n🧹 Memulai proses data cleaning...")
    original_count = len(df)

    #Step 1: Duplikat
    print("\nStep 1: Menghapus transaksi duplikat...")
    df = df.drop_duplicates(subset=['transaction_id'])
    step1_count = len(df)
    print(f" ✓ Dihapus: {original_count - step1_count} baris")
    print(f" ✓ Sisa: {step1_count} baris")

    #Step 2: Transaksi gagal
    print("\nStep 2: Menghapus transaksi yang gagal (status='failed')...")
    df = df[df['status'] == 'success']
    step2_count = len(df)
    print(f" ✓ Dihapus: {step1_count - step2_count} baris")
    print(f" ✓ Sisa: {step2_count} baris")

    #Step 3: Amount tidak valid
    print("\nStep 3: Menghapus transaksi dengan amount <= 0...")
    df = df[df['amount'] > 0]
    step3_count = len(df)
    print(f" ✓ Dihapus: {step2_count - step3_count} baris")
    print(f" ✓ Sisa: {step3_count} baris")

    #Step 4: Transaksi ke diri sendiri
    print("\nStep 4: Menghapus transaksi dari pengirim ke dirinya sendiri...")
    df = df[df['sender_account'] != df['receiver_account']]
    step4_count = len(df)
    print(f" ✓ Dihapus: {step3_count - step4_count} baris")
    print(f" ✓ Sisa: {step4_count} baris")

    #Step 5: Standarisasi timestamp
    print("\nStep 5: Standarisasi format timestamp...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.day_name()

    #Tandai transaksi di jam mencurigakan (23:00 - 04:00)
    df['is_odd_hours'] = df['hour'].apply(
        lambda x: True if (x >= 23 or x <= 4) else False
    )

    print(f" ✓ Timestamp berhasil distandarisasi.")
    print(f" ✓ Transaksi di jam mencurigakan: {df['is_odd_hours'].sum()}")

    #Step 6: Tambah kolom berguna
    print("\nStep 6: Menambah kolom analisis tambahan...")

    #Step 7: Hapus baris yang rekeningnya kosong (NaN)
    print("\nStep 7: Menghapus data dengan rekening kosong...")
    df = df.dropna(subset=['sender_account', 'receiver_account'])

    #Kategorisasi amount
    def categorize_amount(amount):
        if amount < 500000:
            return 'Kecil'  #< 500.000
        elif amount < 500000:
            return 'Sedang'  #500.000 - 5.000.000
        elif amount < 50000000:
            return 'Besar'  #5.000.000 - 50.000.000
        else:
            return 'Sangat Besar'  #> 50.000.000
        
    df['amount_category'] = df['amount'].apply(categorize_amount)
    print(f" ✓ Kategori amount ditambahkan.")

    #Reset index
    df = df.reset_index(drop=True)

    #Summary
    print(f"\n📊 Hasil Cleaning: ")
    print(f"Data awal: {original_count} baris")
    print(f"Data bersih: {len(df)} baris")
    print(f"Dihapus total: {original_count - len(df)} baris")
    print(f"Persentase tersisa: {len(df)/original_count * 100:.1f}%")

    return df

def check_data_quality(df):
    """Cek kualitas data setelah cleaning"""
    print("\n🔍 Cek Kualitas Data: ")
    print(f"Missing values: \n{df.isnull().sum()}")
    print(f"\n Tipe data:\n{df.dtypes}")
    print(f"\n Statistik amount: ")
    print(f"Min: Rp{df['amount'].min():,.0f}")
    print(f"Max: Rp{df['amount'].max():,.0f}")
    print(f"Rata-rata: Rp{df['amount'].mean():,.0f}")
    print(f"Median: Rp{df['amount'].median():,.0f}")

def save_clean_data(df, output_dir='data/processed'):
    """Simpan data bersih"""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'transactions_clean.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✅ Data bersih disimpan: {output_path}")

if __name__ == "__main__":
    #Load data
    users, transactions = load_data()

    #Clean transactions
    clean_df = clean_transactions(transactions)

    #Cek kualitas
    check_data_quality(clean_df)

    #Simpan
    save_clean_data(clean_df)

    print("\n🎉 Data cleaning selesai!")
"""
Script untuk generate data dummy transaksi keuangan.
Data ini mensimulasikan jaringan transaksi yang mengandung mule account
"""

import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta
import os

#Inisialisasi Faker dengan locale Indonesia
fake = Faker('id_ID')

#Set random seed agar hasil bisa direproduksi (hasilnya selalu sama setiap dijalankan)
random.seed(42)
np.random.seed(42)

def generate_account_id():
    """Generate nomor rekening format Indonesia (16 digit)"""
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])

def generate_users(n_normal=100, n_mule=15):
    """
    Generate daftar user.

    Parameter:
    - n_normal: jumlah user normal
    - n_mule: jumlah mule account (yang mencurigakan)

    Return:
    - DataFrame berisi data user
    """

    users = []

    #Generate user normal
    for i in range(n_normal):
        users.append({
            'user_id': f'USER_{i+1:04d}',
            'name': fake.name(),
            'account_id': generate_account_id(),
            'account_type': random.choice(['Tabungan', 'Giro']),
            'is_mule': False #Label sebenarnya (untuk validasi)
        })
    
    #Generate mule account (ditandai is_mule=True untuk validasi)
    for i in range(n_mule):
        users.append({
            'user_id': f'MULE_{i+1:04d}',
            'name': fake.name(),
            'account_id': generate_account_id(),
            'account_type': 'Tabungan',
            'is_mule': True
        })
    
    #Acak urutan agar mule tidak terlihat di baris terakhir
    df = pd.DataFrame(users)
    df = df.sample(frac=1).reset_index(drop=True)

    return df

def generate_transactions(users_df, n_transactions=500):
    """
    Generate data transaksi dengan pola realistis.

    Pola yang disimulasikan:
    1. Transaksi normal: jumlah sedang, tidak terlalu sering
    2. Transaksi mule: menerima dari banyak sumber, lalu kirim ke satu tujuan

    Parameter:
    - users_df: DataFrame user yang sudah dibuat
    - n_transactions: total jumlah transaksi

    Return:
    - DataFrame berisi data transaksi
    """
    transactions = []

    #Pisahkan user normal dan mule
    normal_users = users_df[users_df['is_mule'] == False]
    mule_users = users_df[users_df['is_mule'] == True]

    #Tanggal mulai simulasi (30 hari ke belakang dari hari ini)
    start_date = datetime.now() - timedelta(days=30)

    #Pola 1: Transaksi Normal
    #User biasa transfer ke user lain sesekali
    n_normal_tx = int(n_transactions * 0.6)  #60% transaksi normal
    
    for i in range(n_normal_tx):
        sender = normal_users.sample(1).iloc[0]
        receiver = normal_users.sample(1).iloc[0]

        #Pastikan pengirim dan penerima berbeda
        while sender['user_id'] == receiver['user_id']:
            receiver = normal_users.sample(1).iloc[0]
        
        #Waktu transaksi acak dalam 30 hari terakhir
        tx_time = start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        transactions.append({
            'transaction_id': f'TXN_{len(transactions)+1:06d}',
            'timestamp': tx_time,
            'sender_id': sender['user_id'],
            'sender_account': sender['account_id'],
            'receiver_id': receiver['user_id'],
            'receiver_account': receiver['account_id'],
            'amount': round(random.uniform(50000, 5000000), 2),  #50 ribu - 5 juta
            'transaction_type': random.choice(['Transfer', 'Payment', 'Purchase']),
            'status': 'success' if random.random() > 0.05 else 'failed',
            'notes': random.choice(['', 'Pembayaran', 'Hutang', 'Belanja', ''])
        })
    
    #Pola 2: Transaksi Mule (Mencurigakan)
    #Banyak orang mengirim ke satu mule, lalu mule kirim ke satu akun
    n_mule_tx = int(n_transactions * 0.4)  #40% transaksi mencurigakan

    #Tentukan "master account" - tujuan akhir uang haram
    #Ini adalah akun yang dikendalikan oleh bos kriminal
    master_account_id = f'MASTER_{generate_account_id()}'
    master_user_id = 'CRIMINAL_BOSS'

    for i in range(n_mule_tx):
        mule = mule_users.sample(1).iloc[0]

        if random.random() < 0.65:
            #Banyak orang (normal) kirim ke mule
            sender = normal_users.sample(1).iloc[0]
            receiver = mule
            amount = round(random.uniform(100000, 2000000), 2)  #Jumlah lebih besar
            notes = random.choice(['Transfer', '', 'Investasi', 'Kerjasama'])
        else:
            #Mule kirim ke master account (pengiriman ke bos)
            sender = mule
            #Sesekali mule transfer ke mule lain (layering)
            if random.random() < 0.3:
                receiver = mule_users.sample(1).iloc[0]
                while receiver['user_id'] == sender['user_id']:
                    receiver = mule_users.sample(1).iloc[0]
                notes = 'Transfer'
            else:
                #Kirim ke master
                receiver = pd.Series({
                    'user_id': master_user_id,
                    'account_id': master_account_id
                })
                notes = ''
            amount = round(random.uniform(500000, 10000000), 2)  #Jumlah besasr
        
        #Mule biasanya transaksi di luar jam normal (malam hari)
        tx_time = start_date + timedelta(
            days=random.randint(0, 30),
            hours=random.choice([0, 1, 2, 3, 22, 23]),  #Jam mencurigakan
            minutes=random.randint(0, 59)
        )

        transactions.append({
            'transaction_id': f'TXN_{len(transactions)+1:06d}',
            'timestamp': tx_time,
            'sender_id': sender['user_id'],
            'sender_account': sender['account_id'],
            'receiver_id': receiver['user_id'],
            'receiver_ammount': receiver['account_id'],
            'amount': amount,
            'transaction_type': 'Transfer',
            'status': 'success',
            'notes': notes
        })
    
    #Acak urutan transaksi berdasarkan waktu
    df = pd.DataFrame(transactions)
    df = df.sort_values('timestamp').reset_index(drop=True)

    return df

def save_data(users_df, transactions_df, output_dir='data/raw'):
    """Simpan data ke file CSV"""
    os.makedirs(output_dir, exist_ok=True)

    users_path = os.path.join(output_dir, 'users.csv')
    tx_path = os.path.join(output_dir, 'transactions_raw.csv')

    users_df.to_csv(users_path, index=False)
    transactions_df.to_csv(tx_path, index=False)

    print(f"✅ Data user disimpan: {users_path}")
    print(f"✅ Data transaksi disimpan: {tx_path}")
    print(f"\n📊 Statistik Data: ")
    print(f"Total user: {len(users_df)}")
    print(f"User normal: {len(users_df[users_df['is_mule']==False])}")
    print(f"Male account: {len(users_df[users_df['is_mule']==True])}")
    print(f"Total transaksi: {len(transactions_df)}")
    print(f"Nilai total: Rp {transactions_df['amount'].sum():,.0f}")

if __name__ == "__main__":
    print("🚀 Memulai generate data dummy...")

    #Generate users
    print("\n.1 Generating users...")
    users = generate_users(n_normal=100, n_mule=15)
    print(f" ✓ {len(users)} user berhasil dibuat")

    #Generate transactions
    print("\n2. Generating transactions...")
    transactions = generate_transactions(users, n_transactions=800)
    print(f" ✓ {len(transactions)} transaksi berhasil dibuat")

    #Tampilkan preview
    print("\n3. Preview data: ")
    print("\nUser (5 baris pertama): ")
    print(users.head())
    print("\nTransaksi (5 baris pertama): ")
    print(transactions.head())

    #Simpan data
    print("\n4. Menyimpan data...")
    save_data(users, transactions)

    print("\n🎉 Data generation selesai!")

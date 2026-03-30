"""
Script untuk analisis graph menggunakan berbagai algoritma:
1. PageRank - untuk menemukan node paling berpengaruh
2. Betweenness Centrality - node yang sering jadi perantara
3. In-degree/Out-degree Analysis
4. Community Detection (bonus)
"""

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os

def calculate_pagerank(G, alpha=0.85, max_iter=100):
    """
    Hitung PageRank untuk setiap node.

    Parameter:
    - G: NetworkX DiGraph
    - alpha: damping factor (standar 0.85 - jangan diubah kecuali tahu alasannya)
    - max_iter: iterasi maksimum

    Return:
    - dict: {account_id: pagerank_score}

    Interpretasi:
    - Skor lebih tinggi = node lebih "central" = lebih mencurigakan sebagai mule
    """
    print("🔄 Menghitung PageRank...")

    pagerank_scores = nx.pagerank(
        G,
        alpha=alpha,  #Damping factor: probabilitas untuk tetap di node saat ini
        weight='weight',  #Gunakan berat edge (total amount transaksi)
        max_iter=max_iter
    )

    print(f" ✓ PageRank berhasil dihitung untuk {len(pagerank_scores)} node")

    #Normalisasi skor ke skala 0-100 agar mudah dibaca
    max_score = max(pagerank_scores.values())
    min_score = min(pagerank_scores.values())

    pagerank_normalized = {
        node: (score - min_score) / (max_score - min_score) * 100
        for node, score in pagerank_scores.items()
    }

    return pagerank_scores, pagerank_normalized

def calculate_betweenness_centrality(G):
    """
    Hitung Betweenness Centrality.

    Betweenness = seberapa sering node ini menjadi "jembatan" dalam jalur terpendek antara dua node lain.

    Mule account biasanya memiliki betweenness tinggi karena mereka menjadi perantara antara sumber kejahatan dan tujuan akhir uang.
    """
    print("🔄 Menghitung Betweenness Centrality (ini mungkin memakan waktu beberapa menit)...")

    #Untuk graph besar, gunakan approximation
    if G.number_of_nodes() > 500:
        print("ℹ️ Graph besar terdeteksi, menggunakan approximation...")
        bc_scores = nx.betweenness_centrality(G, k=100, weight='weight')
    else:
        bc_scores = nx.betweenness_centrality(G, weight='weight')
    
    print(f" ✓ Betweenness Centrality berhasil dihitung")

    return bc_scores

def calculate_degree_metrics(G):
    """
    Hitung metrik degree untuk setiap node:
    - in_degree: jumlah yang mengirim ke node ini
    - out_degree: jumlah yang menerima dari node ini
    - degree_ratio: rasio in/out (mule biasanya in >> out awalnya)
    """
    metrics = {}

    for node in G.nodes():
        in_d = G.in_degree(node)
        out_d = G.out_degree(node)

        #Total amount received
        in_edges = G.in_edges(node, data=True)
        total_received = sum(data.get('weight', 0) for _, _, data in in_edges)

        #Total amount sent
        out_edges = G.out_edges(node, data=True)
        total_sent = sum(data.get('weight', 0) for _, _, data in out_edges)

        metrics[node] = {
            'in_degree': in_d,
            'out_degree': out_d,
            'total_degree': in_d + out_d,
            'degree_ratio': in_d / max(out_d, 1),  #Hindari division by zero
            'total_received': total_received,
            'total_sent': total_sent,
            'net_flow': total_received - total_sent,
            'flow_ratio': total_received / max(total_sent, 1)
        }

    return metrics

def compile_analysis_results(G, pagerank_raw, pagerank_norm, bc_scores, degree_metrics):
    """
    Gabungkan semua hasil analisis ke dalam satu DataFrame.
    Ini yang akan digunakan untuk fraud detection.
    """
    print("\n📋 Menggabungkan hasil analisis....")

    results = []

    for node in G.nodes():
        dm = degree_metrics.get(node, {})
        results.append({
            'account_id': node,
            'pagerank_raw': pagerank_raw.get(node, 0),
            'pagerank_score': pagerank_norm.get(node, 0),
            'betweenness_centrality': bc_scores.get(node, 0),
            'in_degree': dm.get('in_degree', 0),
            'out_degree': dm.get('out_degree', 0),
            'total_degree': dm.get('total_degree', 0),
            'degree_ratio': dm.get('degree_ratio', 0),
            'total_received': dm.get('total_received', 0),
            'total_sent': dm.get('total_sent', 0),
            'net_flow': dm.get('net_flow', 0),
            'flow_ratio': dm.get('flow_ratio', 0),
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values('pagerank_score', ascending=False).reset_index(drop=True)
    df['rank'] = df.index + 1

    print(f" ✓ Hasil analisis digabung: {len(df)} akun")

    return df

def print_top_suspects(df, top_n=10):
    """Cetak top N akun yang paling mencurigakan berdasarkan PageRank"""
    print(f"\n🎯 Top {top_n} Akun dengan PageRank Tertinggi (Kandidat Mule): ")
    print("-" * 80)
    print(f"{'Rank':<5} {'Account':<20} {'PageRank':<12} {'InDeg':<8} {'OutDeg':<8} {'Total Terima':<15}")
    print("-" * 80)

    for _, row in df.head(top_n).iterrows():
        print(f"{row['rank']:<5} {str(row['account_id'])[:18]:<20}"
              f"{row['pagerank_score']:<12.2f}"
              f"{row['in_degree']:<8}"
              f"{row['out_degree']:<8}"
              f"Rp{row['total_received']:>12,.0f}")

def visualize_pagerank_distribution(df, output_path='docs/images/pagerank_dist.png'):
    """Visualisasi distribusi skor PageRank"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    #Plot 1: Distribusi skor PageRank
    axes[0].hist(df['pagerank_score'], bins=30, color='steelblue', edgecolor='white', alpha=0.8)
    axes[0].set_title('Distribusi Skor PageRank', fontsize=14)
    axes[0].set_ylabel('Jumlah Akun')
    axes[0].axvline(df['pagerank_score'].quantile(0.95), color='red', linestyle='--', label='Persentil 95 (Threshold)')
    axes[0].legend()

    #Plot 2: Scatter plot PageRank vs In-Degree
    scatter = axes[1].scatter(
        df['in_degree'],
        df['pagerank_score'],
        c=df['total_received'],
        cmap='YlOrRd',
        alpha=0.6,
        s=50
    )
    axes[1].set_title('PageRank vs In-Degree', fontsize=14)
    axes[1].set_xlabel('In-Degree (Jumlah pengirim)')
    axes[1].set_ylabel('Skor PageRank')
    plt.colorbar(scatter, ax=axes[1], label='Total Uang Diterima')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✅ Visualisasi PageRank disimpan: {output_path}")

def detect_communities(G):
    """
    Deteksi komunitas menggunakan Lovain Algorithm.
    Satu komunitas = satu jaringan sindikat.
    """
    try:
        import community as community_louvain
    except ImportError:
        print("\n⚠️ Install dulu: pip install python-louvain")
        return {}, {}
    
    #Louvain bekerja pada undirected graph
    G_undirected = G.to_undirected()

    #Deteki komunitas
    partition = community_louvain.best_partition(G_undirected)

    #Hitung statistik per komunitas
    community_stats = {}
    for node, comm_id in partition.items():
        if comm_id not in community_stats:
            community_stats[comm_id] = {'nodes': [], 'total_amount': 0}

        community_stats[comm_id]['nodes'].append(node)
        community_stats[comm_id]['total_amount'] += G.nodes[node].get('total_received', 0)
    
    print(f"\n🔍 Community Detection: ")
    print(f" ✓ Total komunitas (sindikat) ditemukan: {len(community_stats)}")

    #Urutkan berdasarkan ukuran (banyaknya node/anggota)
    sorted_communities = sorted(
        community_stats.items(),
        key=lambda x: len(x[1]['nodes']),
        reverse=True
    )

    print(f"\n🏆 Top 5 Komunitas Terbesar: ")
    for comm_id, stats in sorted_communities[:5]:
        print(f" - Komunitas {comm_id}: {len(stats['nodes'])} anggota | Total Dana Berputar: Rp{stats['total_amount']:,.0f}")

    return partition, community_stats

if __name__ == "__main__":
    from graph_builder import build_transaction_graph, add_node_statistics

    #Load data
    print("📂 Loading data...")
    transactions = pd.read_csv('data/processed/transactions_clean.csv', dtype={'sender_account':str, 'receiver_account': str})

    #Bangun graph
    G = build_transaction_graph(transactions)
    G = add_node_statistics(G, transactions)

    #Hitung semua metrik
    pagerank_raw, pagerank_norm = calculate_pagerank(G)
    bc_scores = calculate_betweenness_centrality(G)
    degree_metrics = calculate_degree_metrics(G)

    #Gabungkan hasil
    results_df = compile_analysis_results(G, pagerank_raw, pagerank_norm, bc_scores, degree_metrics)

    #Tampilkan top suspects
    print_top_suspects(results_df, top_n=10)

    partition, community_stats = detect_communities(G)

    #Visualisasi
    visualize_pagerank_distribution(results_df)

    #Simpan hasil
    os.makedirs('data/output', exist_ok=True)
    results_df.to_csv('data/output/analysis_results.csv', index=False)
    print("\n✅ Hasil analisis disimpan: data/output/analysis_results.csv")

    print("\n🎉 Graph analysis selesai!")
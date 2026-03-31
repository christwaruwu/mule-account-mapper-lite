import pandas as pd
import networkx as nx
from pyvis.network import Network
import os

def create_interactive_graph(G, suspicious_accounts, output_path='docs/images/network.html'):
    print("🎨 Membuat visualisasi interaktif...")
    
    # Setup kanvas PyVis
    net = Network(height="700px", width="100%", bgcolor="#1a1a2e", font_color="white", directed=True)
    
    # Pengaturan Fisika Animasi
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 2, 
        "shadow": false
      },
      "edges": {
        "shadow": false, 
        "smooth": {"type": "continuous"}
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "maxVelocity": 50,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": {
          "enabled": true,
          "iterations": 150,
          "updateInterval": 25
        }
      },
      "interaction": {
        "hideEdgesOnDrag": true,
        "hideNodesOnDrag": false,
        "navigationButtons": true
      }
    }
    """)
    
    # Pastikan list akun mencurigakan semuanya berbentuk string
    suspicious_set = set(str(acc) for acc in suspicious_accounts)
    
    # Proses Node (Titik Rekening)
    for node in G.nodes():
        node_str = str(node) # UBAH JADI STRING MURNI DI SINI
        node_data = G.nodes[node]
        in_degree = node_data.get('in_degree', 0)
        out_degree = node_data.get('out_degree', 0)
        total_received = node_data.get('total_received', 0)
        total_sent = node_data.get('total_sent', 0)
        
        is_suspicious = node_str in suspicious_set
        
        if is_suspicious:
            color = '#ff4444' # Merah
            size = min(50, in_degree * 5 + 15)
            title = f"<b>🚨 MENCURIGAKAN</b><br>Account: {node_str}<br>Penerima dari: {in_degree} rekening<br>Total Terima: Rp{total_received:,.0f}"
        else:
            color = '#4488ff' # Biru
            size = min(30, in_degree * 3 + 10)
            title = f"Account: {node_str}<br>Penerima dari: {in_degree} rekening<br>Total Terima: Rp{total_received:,.0f}"
            
        # Gunakan node_str (bukan node asli)
        net.add_node(node_str, label=node_str[:8] + '...', title=title, color=color, size=size,
                     borderWidth=3 if is_suspicious else 1, borderWidthSelected=5)
        
    # Proses Edge (Garis Transaksi)
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 0)
        count = data.get('count', 1)
        width = min(10, count * 0.5 + 1)
        
        # Gunakan str(u) dan str(v) untuk menghindari error numpy
        net.add_edge(str(u), str(v), width=width, title=f"Transaksi: {count}x<br>Total: Rp{weight:,.0f}",
                     color='rgba(255, 100, 100, 0.7)' if str(u) in suspicious_set else 'rgba(200, 200, 200, 0.5)')
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    net.save_graph(output_path)
    print(f"   ✓ Visualisasi interaktif disimpan: {output_path}")
    return output_path

# ==========================================
# INI ADALAH MESIN PENGGERAKNYA (PENTING!)
# ==========================================
if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from graph_builder import build_transaction_graph, add_node_statistics
    
    print("📂 Loading data...")
    # SOLUSI: Tambahkan dtype untuk memaksa Pandas membaca nomor rekening sebagai Teks murni
    transactions = pd.read_csv('data/processed/transactions_clean.csv', 
                               dtype={'sender_account': str, 'receiver_account': str})
    suspicious_df = pd.read_csv('data/output/suspicious_accounts.csv', 
                                dtype={'account_id': str})
    
    G = build_transaction_graph(transactions)
    G = add_node_statistics(G, transactions)
    
    suspicious_list = suspicious_df['account_id'].tolist()
    
    create_interactive_graph(G, suspicious_list)
    print("\n🎉 Sukses! File network.html sudah siap digunakan.")
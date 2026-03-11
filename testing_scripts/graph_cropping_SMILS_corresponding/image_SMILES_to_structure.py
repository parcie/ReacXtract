# smiles_to_graph.py
import os
from rdkit import Chem
from rdkit.Chem import Draw
import networkx as nx
import matplotlib.pyplot as plt

def smiles_to_graph(smiles, folder="output", name="molecule"):
    # Ensure the folder exists
    os.makedirs(folder, exist_ok=True)

    # Convert SMILES to molecule
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES string!")

    # Save 2D depiction with RDKit
    structure_path = os.path.join(folder, f"{name}_structure.png")
    Draw.MolToFile(mol, structure_path, size=(300, 300))
    print(f"2D structure saved as {structure_path}")

    # Convert to NetworkX graph
    G = nx.Graph()
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx(), label=atom.GetSymbol())

    for bond in mol.GetBonds():
        G.add_edge(bond.GetBeginAtomIdx(),
                   bond.GetEndAtomIdx(),
                   label=str(bond.GetBondType()))

    # Draw and save NetworkX graph
    pos = nx.spring_layout(G, seed=42)  # fixed layout for reproducibility
    labels = nx.get_node_attributes(G, 'label')
    edge_labels = nx.get_edge_attributes(G, 'label')

    plt.figure(figsize=(6,6))
    nx.draw(G, pos, labels=labels, with_labels=True,
            node_color='lightblue', node_size=1000, font_size=10)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    plt.title("Molecular Graph")

    graph_path = os.path.join(folder, f"{name}_graph.png")
    plt.savefig(graph_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Graph image saved as {graph_path}")

    return G

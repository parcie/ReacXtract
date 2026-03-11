import os
import matplotlib.font_manager as fm
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Create DataFrame from the table data (manually entered based on user's image)
data = {
    'page_index': list(range(9, 42)),
    'cos_similarity_whole_page': [
        0.9868, 0.8839, 0.9249, 0.9186, 0.7671, 0.8256, 0.9882, 0.9836, 0.9861, 0.9009,
        0.8891, 0.9891, 0.8537, 0.8598, 0.84, 0.914, 0.9103, 0.9021, 0.9291, 0.9719,
        0.9729, 0.957, 0.904, 0.9156, 0.9346, 0.9421, 0.9868, 0.9612, 0.9849, 0.9115,
        0.9048, 0.8787, 0.9758
    ],
    'P_whole_page': [
        0.9477, 0.8918, 0.8897, 0.8804, 0.8669, 0.879, 0.9462, 0.9466, 0.9631, 0.8945,
        0.89, 0.9719, 0.8996, 0.8948, 0.898, 0.8937, 0.9081, 0.8697, 0.897, 0.9617,
        0.9508, 0.9123, 0.9094, 0.9247, 0.9094, 0.9282, 0.9438, 0.922, 0.8973, 0.9171,
        0.8822, 0.8767, 0.9369
    ],
    'R_whole_page': [
        0.9586, 0.9201, 0.9269, 0.9187, 0.8918, 0.8758, 0.9562, 0.9609, 0.9699, 0.8945,
        0.9165, 0.9756, 0.9148, 0.9104, 0.8802, 0.8845, 0.9024, 0.8775, 0.8774, 0.9601,
        0.9582, 0.9246, 0.9184, 0.9302, 0.9329, 0.9307, 0.9497, 0.9295, 0.9134, 0.928,
        0.9167, 0.9025, 0.9339
    ],
    'F1_whole_page': [
        0.9531, 0.9057, 0.9079, 0.8991, 0.8792, 0.8774, 0.9511, 0.9537, 0.9665, 0.9078,
        0.9031, 0.9737, 0.9071, 0.9026, 0.8891, 0.8891, 0.9053, 0.8736, 0.8871, 0.9609,
        0.9545, 0.9184, 0.9139, 0.9274, 0.921, 0.9294, 0.9467, 0.9258, 0.9053, 0.9225,
        0.8991, 0.8895, 0.9354
    ],
    'para_cos_similarity': [
        0.6821, 0.7906, 0.7914, 0.786, 0.7274, 0.6755, 0.8827, 0.9022, 0.9156, 0.799,
        0.6993, 0.9216, 0.8456, 0.8239, 0.7742, 0.762, 0.77, 0.7887, 0.6998, 0.9076,
        0.8572, 0.7945, 0.6017, 0.7603, 0.7998, 0.7944, 0.8811, 0.8836, 0.8894, 0.5941,
        0.85, 0.8162, 0.7824
    ],
    'para_P': [
        0.8589, 0.9413, 0.9462, 0.9403, 0.9018, 0.9172, 0.9669, 0.974, 0.9788, 0.9387,
        0.9263, 0.9787, 0.918, 0.9145, 0.8643, 0.8588, 0.8897, 0.8955, 0.9254, 0.9709,
        0.9637, 0.9445, 0.9015, 0.9401, 0.9597, 0.9388, 0.9676, 0.9594, 0.9565, 0.9017,
        0.93, 0.9356, 0.9584
    ],
    'para_R': [
        0.9405, 0.9361, 0.9546, 0.9601, 0.9359, 0.9438, 0.9657, 0.9639, 0.9707, 0.9561,
        0.9493, 0.9657, 0.921, 0.9129, 0.9203, 0.9114, 0.9142, 0.9312, 0.9355, 0.973,
        0.9602, 0.9452, 0.932, 0.9523, 0.9555, 0.952, 0.9726, 0.9617, 0.9611, 0.9057,
        0.9491, 0.9443, 0.9612
    ],
    'para_F1': [
        0.8978, 0.9339, 0.9495, 0.9484, 0.9155, 0.9272, 0.9624, 0.9689, 0.9747, 0.9423,
        0.9325, 0.9721, 0.9195, 0.9135, 0.8846, 0.8797, 0.9009, 0.9128, 0.9132, 0.9702,
        0.9619, 0.9418, 0.9126, 0.9435, 0.9576, 0.9406, 0.969, 0.9583, 0.957, 0.8961,
        0.9351, 0.9397, 0.9591
    ]
}

df = pd.DataFrame(data)  # assuming 'data' is defined
df.set_index('page_index', inplace=True)

# === Font settings ===
# Option 1: Use a known system font
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.unicode_minus'] = False

# # Option 2 (Optional): Use a specific TTF font
# font_path = 'C:/Windows/Fonts/simhei.ttf'  # Example: for Chinese
# custom_font = fm.FontProperties(fname=font_path)
# plt.rcParams['font.family'] = custom_font.get_name()

# === Plot heatmap ===
plt.figure(figsize=(14, 10))
sns.heatmap(df, cmap='YlGnBu', annot=False, linewidths=0.5, linecolor='gray')
plt.title("Page-wise Similarity Scores Heatmap")
plt.xlabel("Metric")
plt.ylabel("Page Index")
plt.tight_layout()

# === Save figure ===
output_folder = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1"# Change to your target folder
os.makedirs(output_folder, exist_ok=True)
save_path = os.path.join(output_folder, "similarity_heatmap.png")
plt.savefig(save_path, dpi=600, bbox_inches='tight')
plt.close()

print(f"Heatmap saved to: {save_path}")
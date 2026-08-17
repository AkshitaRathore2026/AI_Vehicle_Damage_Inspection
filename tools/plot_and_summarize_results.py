import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Paths
csv_path = r"C:\Users\Lenovo\Desktop\Novadule\AI_Vehicle_Damage_Inspection\runs\detect\ml\outputs\vehicle_damage_yolo\results.csv"
out_dir = os.path.join(os.path.dirname(csv_path), 'analysis')
os.makedirs(out_dir, exist_ok=True)

# Read CSV
try:
    df = pd.read_csv(csv_path)
except Exception as e:
    print(f"Failed to read CSV: {e}")
    sys.exit(1)

# Ensure expected columns exist
metrics_cols = ['metrics/precision(B)', 'metrics/recall(B)', 'metrics/mAP50(B)', 'metrics/mAP50-95(B)']
train_loss_cols = ['train/box_loss', 'train/cls_loss', 'train/dfl_loss']
val_loss_cols = ['val/box_loss', 'val/cls_loss', 'val/dfl_loss']

for c in metrics_cols + train_loss_cols + val_loss_cols + ['epoch']:
    if c not in df.columns:
        print(f"Missing column in CSV: {c}")
        sys.exit(1)

# Prepare series
epochs = df['epoch']
precision = df['metrics/precision(B)']
recall = df['metrics/recall(B)']
mAP50 = df['metrics/mAP50(B)']
mAP5095 = df['metrics/mAP50-95(B)']

train_loss = df[train_loss_cols].sum(axis=1)
val_loss = df[val_loss_cols].sum(axis=1)

# Plot metrics
plt.figure(figsize=(10,6))
plt.plot(epochs, precision, marker='o', label='Precision')
plt.plot(epochs, recall, marker='o', label='Recall')
plt.plot(epochs, mAP50, marker='o', label='mAP@50')
plt.plot(epochs, mAP5095, marker='o', label='mAP@50-95')
plt.xlabel('Epoch')
plt.ylabel('Value')
plt.title('Training metrics')
plt.grid(True)
plt.legend()
metrics_png = os.path.join(out_dir, 'metrics_plot.png')
plt.savefig(metrics_png, bbox_inches='tight', dpi=150)
plt.close()

# Plot losses (train vs val)
plt.figure(figsize=(10,6))
plt.plot(epochs, train_loss, marker='o', label='Train loss (sum)')
plt.plot(epochs, val_loss, marker='o', label='Val loss (sum)')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Train vs Validation Loss (summed components)')
plt.grid(True)
plt.legend()
losses_png = os.path.join(out_dir, 'losses_plot.png')
plt.savefig(losses_png, bbox_inches='tight', dpi=150)
plt.close()

# Summary: best epoch per metric and final epoch snapshot
summary_rows = []
final_epoch = int(epochs.iloc[-1])
for name, series in [("Precision", precision), ("Recall", recall), ("mAP@50", mAP50), ("mAP@50-95", mAP5095)]:
    best_idx = series.idxmax()
    best_epoch = int(epochs.iloc[best_idx])
    best_value = float(series.iloc[best_idx])
    final_value = float(series.iloc[-1])
    summary_rows.append({'metric': name, 'best_value': best_value, 'best_epoch': best_epoch, 'final_value': final_value})

# Save CSV
import csv
summary_csv = os.path.join(out_dir, 'results_summary.csv')
with open(summary_csv, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['metric','best_value','best_epoch','final_value'])
    writer.writeheader()
    for r in summary_rows:
        writer.writerow(r)

# Save human-readable text
summary_txt = os.path.join(out_dir, 'results_summary.txt')
with open(summary_txt, 'w') as f:
    f.write(f"Summary for {csv_path}\n")
    f.write(f"Final epoch: {final_epoch}\n\n")
    for r in summary_rows:
        f.write(f"Metric: {r['metric']}\n")
        f.write(f"  Best value: {r['best_value']:.6f} at epoch {r['best_epoch']}\n")
        f.write(f"  Final value: {r['final_value']:.6f}\n\n")
    f.write('Generated plots:\n')
    f.write(f"  - {metrics_png}\n")
    f.write(f"  - {losses_png}\n")

print('Outputs written:')
print(summary_csv)
print(summary_txt)
print(metrics_png)
print(losses_png)

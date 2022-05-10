import os
import sys
import re

import matplotlib.pyplot as plt
import numpy as np


def visualize_loss(losses, val_losses, file_name):
    x = [i + 1 for i in range(len(losses))]
    print(x)
    plt.xlabel("i'th Epoch")
    plt.ylabel("Loss Value")
    plt.title("Loss per Epoch")
    plt.plot(x, losses, "b-", label="loss")
    plt.plot(x, val_losses, "r-", label="val_loss")
    plt.legend()
    path = "./train_graphs/"
    plt.savefig(path + file_name)
    plt.clf()


data_path = "./LSTM/graphing_data/"

files = [i for i in os.listdir(data_path) if i.endswith(".txt")]

pattern_loss = re.compile("loss: \d\.\d\d\d\d - ")
pattern_val_loss = re.compile("val_loss: \d\.\d\d\d\d")

for count, tmp_file in enumerate(files):
    print(tmp_file)
    losses = []
    val_losses = []
    with open(data_path + tmp_file, "rt") as f:
        lines = f.read()
        val_loss_matches = re.findall(pattern_val_loss, lines)
        val_losses = [float(match[-6:]) for match in val_loss_matches]
        loss_matches = re.findall(pattern_loss, lines)
        losses = [float(match[-9:-3]) for match in loss_matches]
    print(len(losses), len(val_losses))
    print(losses)
    print(val_losses)
    visualize_loss(losses, val_losses, f"lstm_losses_model_{count + 1}")

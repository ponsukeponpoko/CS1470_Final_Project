import os
import sys
import numpy as np
from collections import Counter
from sklearn.model_selection import train_test_split

import matplotlib.pyplot as plt

import tensorflow.keras.layers as layers
import tensorflow.keras.models as models
import tensorflow.keras.callbacks as callbacks
import tensorflow.keras.backend as K

from tensorflow.keras.models import load_model

import random

from music21 import converter, instrument, note, chord, stream

# from midi2audio import FluidSynth

# defining function to read MIDI files
def visualize_loss(losses, file_name):
    x = np.arange(1, len(losses)+1)
    plt.xlabel('i\'th Epoch')
    plt.ylabel('Loss Value')
    plt.title('Loss per Epoch')
    plt.plot(x, losses)
    path="./train_graphs/"
    plt.savefig(path+file_name)
    #plt.show()
    
    
def read_midi(file):

    print("Loading Music File:", file)

    notes = []
    notes_to_parse = None

    # parsing a midi file
    midi = converter.parse(file)

    # Getting notes from midi file
    notes_to_parse = midi.recurse()
    # finding whether a particular element is note or a chord
    for element in notes_to_parse:

        # note
        if isinstance(element, note.Note):
            notes.append(str(element.pitch))

        # chord
        elif isinstance(element, chord.Chord):
            notes.append(".".join(str(n) for n in element.normalOrder))

    # # grouping based on different instruments
    # s2 = instrument.partitionByInstrument(midi)

    # # Looping over all the instruments
    # for part in s2.parts:

    #     # select elements of only piano
    #     if "Piano" in str(part):

    #         notes_to_parse = part.recurse()

    #         # finding whether a particular element is note or a chord
    #         for element in notes_to_parse:

    #             # note
    #             if isinstance(element, note.Note):
    #                 notes.append(str(element.pitch))

    #             # chord
    #             elif isinstance(element, chord.Chord):
    #                 notes.append(".".join(str(n) for n in element.normalOrder))

    return np.array(notes)


def lstm(unique_x, unique_y):
    model = models.Sequential()
    model.add(layers.Embedding(len(unique_x), 100, input_length=32, trainable=True))
    model.add(layers.LSTM(128, return_sequences=True))
    model.add(layers.LSTM(128))
    model.add(layers.Dense(256))
    model.add(layers.Activation("relu"))
    model.add(layers.Dense(len(unique_y)))
    model.add(layers.Activation("softmax"))
    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam")
    return model


def wavenet(unique_x, unique_y):
    model = models.Sequential()

    # embedding layer
    model.add(layers.Embedding(len(unique_x), 100, input_length=32, trainable=True))

    model.add(layers.Conv1D(64, 3, padding="causal", activation="relu"))
    model.add(layers.Dropout(0.2))
    model.add(layers.MaxPool1D(2))

    model.add(
        layers.Conv1D(128, 3, activation="relu", dilation_rate=2, padding="causal")
    )
    model.add(layers.Dropout(0.2))
    model.add(layers.MaxPool1D(2))

    model.add(
        layers.Conv1D(256, 3, activation="relu", dilation_rate=4, padding="causal")
    )
    model.add(layers.Dropout(0.2))
    model.add(layers.MaxPool1D(2))

    # model.add(Conv1D(256,5,activation='relu'))
    model.add(layers.GlobalMaxPool1D())

    model.add(layers.Dense(256, activation="relu"))
    model.add(layers.Dense(len(unique_y), activation="softmax"))

    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam")
    return model


def convert_to_midi(prediction_output, output_audio=False):

    offset = 0
    output_notes = []

    # create note and chord objects based on the values generated by the model
    for pattern in prediction_output:

        # pattern is a chord
        if ("." in pattern) or pattern.isdigit():
            notes_in_chord = pattern.split(".")
            notes = []
            for current_note in notes_in_chord:

                cn = int(current_note)
                new_note = note.Note(cn)
                new_note.storedInstrument = instrument.Piano()
                notes.append(new_note)

            new_chord = chord.Chord(notes)
            new_chord.offset = offset
            output_notes.append(new_chord)

        # pattern is a note
        else:

            new_note = note.Note(pattern)
            new_note.offset = offset
            new_note.storedInstrument = instrument.Piano()
            output_notes.append(new_note)

        # increase offset each iteration so that notes do not stack
        offset += 1
    midi_stream = stream.Stream(output_notes)
    midi_stream.write("midi", fp="music.mid")

    # if output_audio:
    #     # using the default sound font in 44100 Hz sample rate
    #     fs = FluidSynth()
    #     fs.midi_to_audio("music.mid", "output.wav")


# specify the path
# path = "schubert/"
path = "./midis/"

# read all the filenames
files = [i for i in os.listdir(path) if i.endswith(".mid") and i.startswith("Alba")]

# reading each midi file
notes_array = np.array([read_midi(path + i) for i in files])

# converting 2D array into 1D array
notes_ = [element for note_ in notes_array for element in note_]

# No. of unique notes
unique_notes = list(set(notes_))
print("number of unique notes:", len(unique_notes))

# computing frequency of each note
freq = dict(Counter(notes_))


# consider only the frequencies
no = [count for _, count in freq.items()]

# set the figure size
plt.figure(figsize=(5, 5))

# plot
plt.hist(no)


frequent_notes = [note_ for note_, count in freq.items() if count >= 50]
print("number of frequent notes:", len(frequent_notes))


# Preparing new musical files of only top notes

new_music = []

for notes in notes_array:
    temp = []
    for note_ in notes:
        if note_ in frequent_notes:
            temp.append(note_)
    new_music.append(temp)

new_music = np.array(new_music)


# Preparing input and output sequences

no_of_timesteps = 32
x = []
y = []

for note_ in new_music:
    for i in range(0, len(note_) - no_of_timesteps, 1):

        # preparing input and output sequences
        input_ = note_[i : i + no_of_timesteps]
        output = note_[i + no_of_timesteps]

        x.append(input_)
        y.append(output)

x = np.array(x)
y = np.array(y)

print("x:", x.shape)
print("y:", y.shape)


# Assigning unique integer to every note

unique_x = list(set(x.ravel()))
x_note_to_int = dict((note_, number) for number, note_ in enumerate(unique_x))

# preparing input sequences
x_seq = []
for i in x:
    temp = []
    for j in i:
        # assigning unique integer to every note
        temp.append(x_note_to_int[j])
    x_seq.append(temp)

x_seq = np.array(x_seq)

# Prepare integer sequences for output data

unique_y = list(set(y))
y_note_to_int = dict((note_, number) for number, note_ in enumerate(unique_y))
y_seq = np.array([y_note_to_int[i] for i in y])

# 80% of data for training, 20% for evaluation

x_tr, x_val, y_tr, y_val = train_test_split(x_seq, y_seq, test_size=0.2, random_state=0)


# Actual model

K.clear_session()

# Using LSTM
model = None
name = ""

if sys.argv[1] == "--wavenet":
    model = wavenet(unique_x, unique_y)
    name = "wavenet"
else:
    model = lstm(unique_x, unique_y)
    name = "lstm"

model.summary()

print("unique x:", len(unique_x))
print("unique y:", len(unique_y))


# Define the callback to save the best model during training

mc = callbacks.ModelCheckpoint(
    f"best_model-{name}.h5",
    monitor="val_loss",
    mode="min",
    save_best_only=True,
    verbose=1,
)

if sys.argv[2] == "--train":
    # Train the model with batch size of 128 for 50 epochs
    history = model.fit(
        np.array(x_tr),
        np.array(y_tr),
        batch_size=128,
        epochs=50,
        # epochs=1,
        validation_data=(np.array(x_val), np.array(y_val)),
        verbose=1,
        callbacks=[mc],
    )

    # Losses
    # https://stackoverflow.com/questions/36952763/how-to-return-history-of-validation-loss-in-keras
    loss_list = (history.history["val_loss"])
    print("loss_list:",loss_list)
    print("name:", f"best_model-{name})
    
    visualize_losses(loss_list, f"best_model"-{name})
# loading best model
# TODO: Will need to manually rename best models in the future
model = load_model(f"best_model-{name}.h5")

# Time to actually compose

ind = np.random.randint(0, len(x_val) - 1)

random_music = x_val[ind]

predictions = []
for i in range(50):

    random_music = random_music.reshape(1, no_of_timesteps)

    prob = model.predict(random_music)[0]
    y_pred = np.argmax(prob, axis=0)
    predictions.append(y_pred)

    random_music = np.insert(random_music[0], len(random_music[0]), y_pred)
    random_music = random_music[1:]
print(predictions)

# Time to convert integers back to notes
x_int_to_note = dict((number, note_) for number, note_ in enumerate(unique_x))
predicted_notes = [x_int_to_note[i] for i in predictions]
print(predicted_notes)

# Convert predictions into musical file
convert_to_midi(predicted_notes, output_audio=True)

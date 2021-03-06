import torch.nn.functional as F
from torch import nn, zeros, cat, bmm
from data import MAX_LENGTH


class EncoderRNN(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(EncoderRNN, self).__init__()
        self.hidden_size = hidden_size

        self.embedding = nn.Embedding(input_size, hidden_size)
        self.gru = nn.GRU(hidden_size, hidden_size)

    def forward(self, input, hidden):
        embedded = self.embedding(input).view(1, 1, -1)
        output, hidden = self.gru(embedded, hidden)
        return output, hidden

    def init_hidden(self):
        return zeros(1, 1, self.hidden_size)


class AttnDecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size, dropout_p=0.1, max_length=MAX_LENGTH):
        super(AttnDecoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.dropout_p = dropout_p
        self.max_length = max_length

        self.embedding = nn.Embedding(self.output_size, self.hidden_size)
        self.attn = nn.Linear(self.hidden_size * 2, self.max_length)
        self.attn_combine = nn.Linear(self.hidden_size * 2, self.hidden_size)
        self.dropout = nn.Dropout(self.dropout_p)
        self.gru = nn.GRU(self.hidden_size, self.hidden_size)
        self.out = nn.Linear(self.hidden_size, self.output_size)

    def forward(self, input, hidden, encoder_outputs):
        embedded = self.embedding(input).view(1, 1, -1)
        embedded = self.dropout(embedded)

        attn = cat((embedded[0], hidden[0]), 1)
        attn = self.attn(attn)

        attn_weights = F.softmax(attn, dim=1)
        attn_weights = attn_weights.unsqueeze(0)
        encoder_outputs = encoder_outputs.unsqueeze(0)
        # 两个tensor的维度必须为3
        attn_applied = bmm(attn_weights, encoder_outputs)

        output = cat((embedded[0], attn_applied[0]), 1)
        output = self.attn_combine(output)
        output = output.unsqueeze(0)

        output = F.relu(output)
        output, hidden = self.gru(output, hidden)

        output = self.out(output[0])
        output = F.log_softmax(output, dim=1)
        return output, hidden, attn_weights

    def init_hidden(self):
        return zeros(1, 1, self.hidden_size)
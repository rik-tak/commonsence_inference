import argparse
import csv

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import gensim
from tqdm import tqdm

from model import BertForSequenceClassification
from dataset import KUCIDatasetForBert


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-path', type=str, required=True, help='path to BERT pretrained model')
    parser.add_argument('--state-path', type=str, required=True, help='path to state_dict')
    parser.add_argument('--data-test', type=str, required=True, help='path to test data')
    parser.add_argument('--batch-size', type=int, default=1, help='batch size')
    parser.add_argument('--gpu-id', type=str, default='0', help='cuda id')
    args = parser.parse_args()

    # prepare dataset
    test_ds = KUCIDatasetForBert(args.data_test, tokenizer_path=args.model_path)
    test_dl = torch.utils.data.DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    gpu_list = list(map(int, args.gpu_id.split(',')))
    print(gpu_list)
    if torch.cuda.is_available():
        device = torch.device('cuda', gpu_list[0])
    else:
        print('cuda is unavailable')
        device = torch.device('cpu')
    print(f'device: {device}')

    config = {'num_labels': 4}
    model = BertForSequenceClassification.from_pretrained(args.model_path, my_config=config)
    model = torch.nn.DataParallel(model).to(device)
    model.load_state_dict(torch.load(args.state_path))

    print('Start prediction')
    model.eval()
    predictions = torch.LongTensor([]).to(device)
    with torch.no_grad():
        for j, data in tqdm(enumerate(test_dl)):
            inputs = {k: v.to(device) for k, v in data.items()}
            y = model(**inputs)
            prediction = torch.argmax(y, dim=1)     # shape (batch, 1)
            predictions = torch.cat((predictions, prediction), dim=0)

    output_path = 'data/prediction/bert_pred.csv'
    choices = ['a', 'b', 'c', 'd']
    with open(output_path, 'w') as f:
        writer = csv.writer(f)
        for i in range(len(test_ds)):
            pred = predictions[i]
            writer.writerow(choices[pred])


if __name__ == '__main__':
    main()

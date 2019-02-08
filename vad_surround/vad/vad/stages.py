import logging
import glob
import os
import json
import sys
import tensorflow as tf
import numpy as np
from surround import Stage, SurroundData

class VadData(SurroundData):
    input_data = None
    output_data = None

    def __init__(self, input_data):
        self.input_data = input_data
        self.output_data = None

class ValidateData(Stage):
    def operate(self, data, config):
        if data.input is None:
            data.error = "The input data was null!"
            return

        # Make sure the data is an array of numbers
        if type(data.input) is not list:
            data.error = "The input data is not an array!"
            return

        if not all([type(sample) is float for sample in data.input]):
            data.error = "The input data was not floats!"
            return
         
class VadDetection(Stage):
    def load_model(self):
        logging.info("loading the model")

        files = glob.glob('models/vad/model.ckpt-*.meta')

        checkpoint_path = None

        if files:
            checkpoint_path, _ = os.path.splitext(files[-1])

        if checkpoint_path == None or not all([os.path.exists(checkpoint_path + x) for x in ['.data-00000-of-00001', '.index', '.meta']]):
            self.error = "Could not load model"
            return
        
        vocab_path = checkpoint_path + ".json"
        if not os.path.exists(vocab_path):
            vocab_path = os.path.join(os.path.dirname(checkpoint_path), 'vocab.json')
        if not os.path.exists(vocab_path):
            self.error = "Could not locate vocab.json"
            return
        
        self.graph = tf.graph() 

        with self.graph.as_default():
            logging.info('loading model: {}'.format(checkpoint_path))
            
            saver = tf.train.import_meta_graph(checkpoint_path + ".meta")
            vocab = None 
            with open(vocab_path, 'r') as fp:
                vocab = json.load(fp)

            self.x = self.graph.get_tensor_by_name(vocab['x'])
            self.y = self.graph.get_tensor_by_name(vocab['y'])            
            self.init = self.graph.get_operation_by_name(vocab['init'])
            self.logits = self.graph.get_tensor_by_name(vocab['logits'])            
            self.ph_n_shuffle = self.graph.get_tensor_by_name(vocab['n_shuffle'])
            self.ph_n_repeat = self.graph.get_tensor_by_name(vocab['n_repeat'])
            self.ph_n_batch = self.graph.get_tensor_by_name(vocab['n_batch'])
            self.n_classes = len(vocab['targets'])

            self.sess = tf.Session()
            saver.restore(self.sess, checkpoint_path)

    def init_stage(self, config):
        self.graph = None
        self.error = None 

        try: 
            self.load_model()
        except:
            self.error = "Failed to load models"

    def operate(self, data, config):
        if self.error is not None:
            data.error = self.error
            return

        sess = self.sess
        x = self.x
        y = self.y
        ph_n_shuffle = self.ph_n_shuffle
        ph_n_repeat = self.ph_n_repeat
        ph_n_batch = self.ph_n_batch
        init = self.init
        logits = self.logits

        input = np.asmatrix(data.input).reshape(-1, x.shape[1])
        dummy = np.zeros((input.shape[0], ), dtype=np.int32)

        sess.run(init, feed_dict = { x: input, y: dummy, ph_n_shuffle: 1, ph_n_repeat: 1, ph_n_batch: input.shape[0] })
        output = sess.run(logits)
        output = np.mean(output, axis=0)

        data.output = output
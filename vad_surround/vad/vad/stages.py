import logging
import tensorflow as tf
from surround import Stage, SurroundData

class VadData(SurroundData):
    input_data = None
    output_data = None

    def __init__(self, input_data):
        self.input_data = input_data
        self.output_data = None

class ValidateData(Stage):
    def operate(self, data, config):
        data.output_data = "TODO: Validate input data assumptions here"

class VadDetection(Stage):
    def operate(self, data, config):
        pass 

from omegaconf import DictConfig, ListConfig, OmegaConf
import omegaconf
import tensorflow as tf
from tensorflow import keras
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from src.models.decoder.UNetDecoder import UNetDecoder
from src.models.decoder.RNNDecoder import LSTMDecoder, GRUDecoder
from src.models.decoder.TransformerDecoder import TransformerEncoder
from src.models.decoder.RelativeTransformerDecoder import RelativeTransformerEncoder
from src.models.decoder.HGTransformerDecoder import HGTransformerDecoder
from src.models.feature_extractor.CNN import CNN, SeparableCNN

class DualModel(keras.Model):
    def __init__(self, feature_extractor_cfg: DictConfig, decoder_cfg:DictConfig, feature_shape:tuple[int]):
        super().__init__()
        if not isinstance(feature_extractor_cfg, dict):
            feature_extractor_cfg = OmegaConf.to_object(feature_extractor_cfg)
        if not isinstance(decoder_cfg, dict):
            decoder_cfg = OmegaConf.to_object(decoder_cfg)
        self.feature_extractor_cfg = feature_extractor_cfg
        self.decoder_cfg = decoder_cfg
        self.feature_shape = feature_shape
        self.reshape_layer = keras.layers.Reshape((feature_shape[0], feature_shape[1]*feature_shape[2]))
        self.feature_extractor = get_feature_extractor(feature_extractor_cfg)
        self.decoder = get_decoder(decoder_cfg)

    def call(self, inputs):
        x = self.feature_extractor(inputs)
        x = self.reshape_layer(x)
        outputs = self.decoder(x)
        return outputs
    
    def get_config(self):
        config = super().get_config()
        config.update({"feature_extractor_cfg": self.feature_extractor_cfg,
                       'decoder_cfg': self.decoder_cfg,
                       'feature_shape': self.feature_shape})
        return config
    
    
def get_feature_extractor(cfg: dict):
    if cfg['name'] == 'CNN':
        feature_extractor = CNN(list(cfg['params']['base_filters']), list(cfg['params']['kernel_sizes']), cfg['params']['strides'], cfg['params']['pooling'])
    if cfg['name'] == 'SeparableCNN':
        feature_extractor = SeparableCNN(list(cfg['params']['base_filters']), list(cfg['params']['kernel_sizes']), cfg['params']['strides'], cfg['params']['pooling'])

    return feature_extractor

def get_decoder(cfg: DictConfig):
    if cfg['name'] == 'UNetDecoder':
        decoder = UNetDecoder(cfg['params']['n_classes'], cfg['params']['scale_factor'], cfg['params']['se'], cfg['params']['res'], cfg['params']['dropout'])
    elif cfg['name'] == 'LSTMDecoder':
        decoder = LSTMDecoder(cfg['params']['n_classes'], cfg['params']['hidden_size'], cfg['params']['n_layers'], cfg['params']['dropout'])
    elif cfg['name'] == 'GRUDecoder':
        decoder = GRUDecoder(cfg['params']['n_classes'], cfg['params']['hidden_size'], cfg['params']['n_layers'], cfg['params']['dropout'])
    elif cfg['name'] == 'TransformerDecoder':
        decoder = TransformerEncoder(cfg['params']['n_classes'], cfg['params']['n_layers'], cfg['params']['intermediate_dim'], cfg['params']['intermediate_dim'], cfg['params']['num_heads'], cfg['params']['dropout'])
    elif cfg['name'] == 'RelativeTransformerDecoder':
        decoder = RelativeTransformerEncoder(cfg['params']['n_classes'], cfg['params']['n_layers'], cfg['params']['intermediate_dim'], cfg['params']['intermediate_dim'], cfg['params']['num_heads'], cfg['params']['dropout'])
    elif cfg['name'] == 'HGTransformerDecoder':
        decoder = HGTransformerDecoder(cfg['params']['model_name'], cfg['params']['intermediate_dim'], cfg['params']['down_nums'], cfg['params']['dropout'], cfg['params']['n_classes'])
   
    return decoder

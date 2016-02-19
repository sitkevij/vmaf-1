__copyright__ = "Copyright 2016, Netflix, Inc."
__license__ = "LGPL Version 3"

import os
import unittest
import config
from train_test_model import TrainTestModel, NusvrTrainTestModel, \
    LibsvmnusvrTrainTestModel, RandomForestTrainTestModel
from tools import get_stdout_logger, close_logger
import pandas as pd
import numpy as np

class TrainTestModelTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

        self.logger = get_stdout_logger()

        feature_df_file = \
            config.ROOT + \
            "/python/test/resource/sample_feature_extraction_results.json"
        self.feature_df = \
            pd.DataFrame.from_dict(eval(open(feature_df_file, "r").read()))

        self.model_filename = config.ROOT + "/workspace/test_save_load.pkl"
        if os.path.exists(self.model_filename): os.remove(self.model_filename)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

        close_logger(self.logger)

        if os.path.exists(self.model_filename): os.remove(self.model_filename)

    def test_get_xs_ys(self):
        xs = TrainTestModel.get_xs_from_dataframe(self.feature_df, [0, 1, 2])
        expected_xs = { 'ansnr_feat': np.array([46.364271863296779,
                                                42.517841772700201,
                                                35.967123359308225]),
                        'dlm_feat': np.array([ 1.,  1.,  1.]),
                        'ti_feat': np.array([12.632675462694392,
                                             3.7917434352421662,
                                             2.0189066771371684]),
                        'vif_feat': np.array([0.99999999995691546,
                                              0.99999999994743127,
                                              0.9999999999735345])}
        for key in xs: self.assertTrue(all(xs[key] == expected_xs[key]))

        xs = TrainTestModel.get_xs_from_dataframe(self.feature_df)
        for key in xs: self.assertEquals(len(xs[key]), 300)

        ys = TrainTestModel.get_ys_from_dataframe(self.feature_df, [0, 1, 2])
        expected_ys = {'label': np.array([4.5333333333333332,
                                          4.7000000000000002,
                                          4.4000000000000004]),
                       'content_id': np.array([0, 1, 10])}
        self.assertTrue(all(ys['label'] == expected_ys['label']))

        xys = TrainTestModel.get_xys_from_dataframe(self.feature_df, [0, 1, 2])
        expected_xys = { 'ansnr_feat': np.array([46.364271863296779,
                                                 42.517841772700201,
                                                 35.967123359308225]),
                         'dlm_feat': np.array([ 1.,  1.,  1.]),
                         'ti_feat': np.array([12.632675462694392,
                                             3.7917434352421662,
                                             2.0189066771371684]),
                         'vif_feat': np.array([0.99999999995691546,
                                              0.99999999994743127,
                                              0.9999999999735345]),
                         'label': np.array([4.5333333333333332,
                                            4.7000000000000002,
                                            4.4000000000000004]),
                         'content_id': np.array([0, 1, 10])}
        for key in xys: self.assertTrue(all(xys[key] == expected_xys[key]))

    def test_train_save_load_predict(self):

        xys = TrainTestModel.get_xys_from_dataframe(self.feature_df.iloc[:-50])
        xs = TrainTestModel.get_xs_from_dataframe(self.feature_df.iloc[-50:])
        ys = TrainTestModel.get_ys_from_dataframe(self.feature_df.iloc[-50:])

        model = NusvrTrainTestModel({'norm_type':'whiten'}, self.logger)
        model.train(xys)

        model.to_file(self.model_filename)
        self.assertTrue(os.path.exists(self.model_filename))

        loaded_model = NusvrTrainTestModel.from_file(self.model_filename, self.logger)

        result = loaded_model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.10432107750419255)

    def test_train_save_load_predict_libsvmnusvr(self):

        xys = TrainTestModel.get_xys_from_dataframe(self.feature_df.iloc[:-50])
        xs = TrainTestModel.get_xs_from_dataframe(self.feature_df.iloc[-50:])
        ys = TrainTestModel.get_ys_from_dataframe(self.feature_df.iloc[-50:])

        model = LibsvmnusvrTrainTestModel({'norm_type':'whiten'}, self.logger)
        model.train(xys)

        model.to_file(self.model_filename)
        self.assertTrue(os.path.exists(self.model_filename))
        self.assertTrue(os.path.exists(self.model_filename + '.model'))

        loaded_model = LibsvmnusvrTrainTestModel.from_file(self.model_filename, self.logger)

        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'],        0.10432107750419255)

        # loaded model generates slight numerical difference
        result = loaded_model.evaluate(xs, ys)
        self.assertEquals(result['MSE'],        0.10432119255314735)

        model.delete(self.model_filename)

    def test_train_predict_nusvr(self):

        # svr is quite sensitive to data normalization

        xys = TrainTestModel.get_xys_from_dataframe(self.feature_df.iloc[:-50])
        xs = TrainTestModel.get_xs_from_dataframe(self.feature_df.iloc[-50:])
        ys = TrainTestModel.get_ys_from_dataframe(self.feature_df.iloc[-50:])

        model = NusvrTrainTestModel(
            {'norm_type':'whiten'}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.10432107750419255)

        model = NusvrTrainTestModel(
            {'norm_type':'rescale_0to1'}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.1058434677183516)

        model = NusvrTrainTestModel(
            {'norm_type':'rescale_minus1to1'}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.096561628579762998)

        model = NusvrTrainTestModel(
            {'norm_type':'none',}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.35463953349016142)

    def test_train_predict_libsvmnusvr(self):

        # libsvmnusvr is bit exact to nusvr

        xys = TrainTestModel.get_xys_from_dataframe(self.feature_df.iloc[:-50])
        xs = TrainTestModel.get_xs_from_dataframe(self.feature_df.iloc[-50:])
        ys = TrainTestModel.get_ys_from_dataframe(self.feature_df.iloc[-50:])

        model = LibsvmnusvrTrainTestModel(
            {'norm_type':'whiten'}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.10432107750419255)

        model = LibsvmnusvrTrainTestModel(
            {'norm_type':'rescale_0to1'}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.1058434677183516)

        model = LibsvmnusvrTrainTestModel(
            {'norm_type':'rescale_minus1to1'}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.096561628579762998)

        model = LibsvmnusvrTrainTestModel(
            {'norm_type':'none'}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.35463953349016142)


    def test_train_predict_randomforest(self):

        # random forest don't need proper data normalization

        xys = TrainTestModel.get_xys_from_dataframe(self.feature_df.iloc[:-50])
        xs = TrainTestModel.get_xs_from_dataframe(self.feature_df.iloc[-50:])
        ys = TrainTestModel.get_ys_from_dataframe(self.feature_df.iloc[-50:])

        model = RandomForestTrainTestModel({'norm_type':'whiten',
                                'random_state': 0}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.10431733333333336)

        model = RandomForestTrainTestModel({'norm_type':'rescale_0to1',
                                'random_state': 0}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.10431733333333339)

        model = RandomForestTrainTestModel({'norm_type':'rescale_minus1to1',
                                'random_state': 0}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.10431733333333339)

        model = RandomForestTrainTestModel({'norm_type':'none', 'random_state': 0}, self.logger)
        model.train(xys)
        result = model.evaluate(xs, ys)
        self.assertEquals(result['MSE'], 0.10431733333333341)


class TrainTestModelTest2(unittest.TestCase):

    def test_read_xs_ys_from_dataframe(self):

        try:
            import pandas as pd
        except ImportError:
            print 'Warning: import pandas fails. Skip test.'
            return

        try:
            import numpy as np
        except ImportError:
            print 'Warning: import numpy fails. Skip test.'
            return

        feature_df_file = config.ROOT + "/python/test/resource/sample_feature_extraction_results.json"
        feature_df = pd.DataFrame.from_dict(eval(open(feature_df_file, "r").read()))

        xs = TrainTestModel.get_xs_from_dataframe(feature_df, [0, 1, 2])
        expected_xs = { 'ansnr_feat': np.array([46.364271863296779,
                                                42.517841772700201,
                                                35.967123359308225]),
                        'dlm_feat': np.array([ 1.,  1.,  1.]),
                        'ti_feat': np.array([12.632675462694392,
                                             3.7917434352421662,
                                             2.0189066771371684]),
                        'vif_feat': np.array([0.99999999995691546,
                                              0.99999999994743127,
                                              0.9999999999735345])}
        for key in xs: self.assertTrue(all(xs[key] == expected_xs[key]))

        xs = TrainTestModel.get_xs_from_dataframe(feature_df)
        for key in xs: self.assertEquals(len(xs[key]), 300)

        ys = TrainTestModel.get_ys_from_dataframe(feature_df, [0, 1, 2])
        expected_ys = {'label': np.array([4.5333333333333332,
                                          4.7000000000000002,
                                          4.4000000000000004]),
                       'content_id': np.array([0, 1, 10])}
        self.assertTrue(all(ys['label'] == expected_ys['label']))

        xys = TrainTestModel.get_xys_from_dataframe(feature_df, [0, 1, 2])
        expected_xys = { 'ansnr_feat': np.array([46.364271863296779,
                                                 42.517841772700201,
                                                 35.967123359308225]),
                         'dlm_feat': np.array([ 1.,  1.,  1.]),
                         'ti_feat': np.array([12.632675462694392,
                                             3.7917434352421662,
                                             2.0189066771371684]),
                         'vif_feat': np.array([0.99999999995691546,
                                              0.99999999994743127,
                                              0.9999999999735345]),
                         'label': np.array([4.5333333333333332,
                                            4.7000000000000002,
                                            4.4000000000000004]),
                         'content_id': np.array([0, 1, 10])}
        for key in xys: self.assertTrue(all(xys[key] == expected_xys[key]))


if __name__ == '__main__':
    unittest.main()

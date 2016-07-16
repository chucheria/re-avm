'''Determine accuracy on validation set YYYYMM of various hyperparameter setting
for AVMs based on 3 models (linear, random forests, gradient boosting regression)

INVOCATION
  python valavm.py FEATURESGROUP-HPS-TESTMONTH [--test] [--outdir OUTDIR]
  where
   TESTMONTH: yyyymm  Month of test data; training uses months just prior
   FEATURES : features to use
               s: just size (lot and house)
               sw: also weath (3 census track wealth features)
               swp: also property features (rooms, has_pool, ...)
               swpn: also neighborhood features (of census tract and zip5)
   HPS      : hyperaparameters to sweep; possible values
               all: sweep all
               best1: sweep just the best 1 in WORKING/rank_models/TEST_MONTH.pickle
   HPCOUNT  : number of hps to use if HPS is a PATH; default 1
   --test   : if present, runs in test mode, output is not usable
   --outddir: if present, write output file to WORKKING/OUTDIR/

NOTE: What is called "test_month" here is called "validation_month" in paper1.
The test_month is here the month used to estimate the generalization error.

INPUTS
 WORKING/samples-train.csv
 WORKING/PATH
   ex: WORKING/rank_models/TEST_MONTH.pickle  HPs for best models

OUTPUTS
 WORKING/valavm/FEAUTRESGROUP-HPS/FEATURESGROUP-HPS-TESTMONTH.pickle

NOTE 1
The codes for the FEATURES are used directly in AVM and Features, so if you
change them here, you must also change then in those two modules.

NOTE 2
The output is in a directory instead of a file so that Dropbox's selective sync
can be used to control the space used on systems.
'''

from __future__ import division

import argparse
import collections
import cPickle as pickle
import numpy as np
import os
import pandas as pd
import pdb
from pprint import pprint
import random
import sys

import arg_type
import AVM
from Bunch import Bunch
from columns_contain import columns_contain
# from Features import Features
import layout_transactions
from Logger import Logger
from Month import Month
from Path import Path
from SampleSelector import SampleSelector
from Timer import Timer
# from TimeSeriesCV import TimeSeriesCV
cc = columns_contain


def make_grid():
    # return Bunch of hyperparameter settings
    return Bunch(
        # HP settings to test across all models
        n_months_back=(1, 2, 3, 6, 12),

        # HP settings to test for ElasticNet models
        alpha=(0.01, 0.03, 0.1, 0.3, 1.0),  # multiplies the penalty term
        l1_ratio=(0.0, 0.25, 0.50, 0.75, 1.0),  # 0 ==> L2 penalty, 1 ==> L1 penalty
        units_X=('natural', 'log'),
        units_y=('natural', 'log'),

        # HP settings to test for tree-based models
        # settings based on Anil Kocak's recommendations
        n_estimators=(10, 30, 100, 300),
        max_features=(1, 'log2', 'sqrt', 'auto'),
        max_depth=(1, 3, 10, 30, 100, 300),

        # HP setting to test for GradientBoostingRegression models
        learning_rate=(.10, .25, .50, .75, .99),
        # experiments demonstrated that the best loss is seldom quantile
        # loss_seq=('ls', 'quantile'),
        loss=('ls',),
    )


def make_control(argv):
    'return a Bunch'

    print argv
    parser = argparse.ArgumentParser()
    parser.add_argument('invocation')
    parser.add_argument('features_hps_month_locality', type=arg_type.features_hps_month_locality)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--outdir')
    arg = parser.parse_args(argv)
    arg.base_name = 'valavm'

    s = arg.features_hps_month_locality.split('-')
    if len(s) == 3:
        arg.features_group, arg.hps, arg.test_month = s
        arg.locality = 'global'
    elif len(s) == 4:
        arg.features_group, arg.hps, arg.test_month, arg.locality = s
    else:
        print 'bad features_hps_month_locality'
        print arg.features_hps_month_locality
        print s
        pdb.set_trace()

    print arg

    random_seed = 123
    random.seed(random_seed)

    dir_working = Path().dir_working()

    # assure output directory exists
    if arg.outdir is None:
        dir_path = dir_working + arg.base_name + '/' + ('%s-%s/') % (arg.features_group, arg.hps)
    else:
        dir_path = dir_working + arg.outdir + '/'
    out_file_name = '%s-%s-%s.pickle' % (arg.features_group, arg.hps, arg.test_month)
    path_out_file = dir_path + out_file_name
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return Bunch(
        arg=arg,
        debug=False,
        path_in_samples=dir_working + 'samples-train.csv',
        path_in_best1=dir_working + 'rank_models/' + arg.test_month + '.pickle',
        path_out_file=path_out_file,
        path_out_log=dir_path + 'log-' + str(arg.test_month) + '.txt',
        grid_seq=make_grid(),
        random_seed=random_seed,
        timer=Timer(),
    )


ResultKeyEn = collections.namedtuple(
    'ResultKeyEn',
    'n_months_back units_X units_y alpha l1_ratio',
)
ResultKeyGbr = collections.namedtuple(
    'ResultKeyGbr',
    'n_months_back n_estimators max_features max_depth loss learning_rate',
)
ResultKeyRfr = collections.namedtuple(
    'ResultKeyRfr',
    'n_months_back n_estimators max_features max_depth',
)
ResultValue = collections.namedtuple(
    'ResultValue',
    'actuals predictions',
)


def make_result_keys(control):
    'return list of ResultKey'
    def en():
        'return list of ResultKenEn'
        result = []
        for n_months_back in control.grid_seq.n_months_back:
            for units_X in control.grid_seq.units_X:
                for units_y in control.grid_seq.units_y:
                    for alpha in control.grid_seq.alpha:
                        for l1_ratio in control.grid_seq.l1_ratio:
                            item = ResultKeyEn(
                                n_months_back=n_months_back,
                                units_X=units_X,
                                units_y=units_y,
                                alpha=alpha,
                                l1_ratio=l1_ratio,
                                )
                            result.append(item)
        return result

    def gbr():
        'return list of ResultKeyGbr'
        result = []
        for n_months_back in control.grid_seq.n_months_back:
            for n_estimators in control.grid_seq.n_estimators:
                for max_features in control.grid_seq.max_features:
                    for max_depth in control.grid_seq.max_depth:
                        for loss in control.grid_seq.loss:
                            for learning_rate in control.grid_seq.learning_rate:
                                item = ResultKeyGbr(
                                    n_months_back=n_months_back,
                                    n_estimators=n_estimators,
                                    max_features=max_features,
                                    max_depth=max_depth,
                                    loss=loss,
                                    learning_rate=learning_rate,
                                    )
                                result.append(item)
        return result

    def rfr():
        'return list of ResultKeyRfr'
        result = []
        for n_months_back in control.grid_seq.n_months_back:
            for n_estimators in control.grid_seq.n_estimators:
                for max_features in control.grid_seq.max_features:
                    for max_depth in control.grid_seq.max_depth:
                        item = ResultKeyRfr(
                            n_months_back=n_months_back,
                            n_estimators=n_estimators,
                            max_features=max_features,
                            max_depth=max_depth,
                            )
                        result.append(item)
        return result

    hps = control.arg.hps
    result = []
    if hps == 'all' or hps == 'en':
        result.extend(en())
    if hps == 'all' or hps == 'gbr':
        result.extend(gbr())
    if hps == 'all' or hps == 'rfr':
        result.extend(rfr())
    return result


def split_samples(samples, test_month, n_months_back):
    'return test, train'
    # NOTE: the test data are in the test month
    # NOTE: the training data are in the previous n_months_back
    test_month = Month(test_month)
    ss = SampleSelector(samples)
    samples_test = ss.in_month(test_month)
    samples_train = ss.between_months(
        test_month.decrement(n_months_back),
        test_month.decrement(1),
        )
    return samples_test, samples_train


def fit_and_run(avm, samples_test, samples_train, features_group):
    'return a ResultValue and Importances'
    def make_importances(model_name, fitted_avm):
        if model_name == 'ElasticNet':
            return {
                    'intercept': fitted_avm.intercept_,
                    'coefficients': fitted_avm.coef_,
                    'features_group': features_group,
                    }
        else:
            # the tree-based models have the same structure for their important features
                return {
                        'feature_importances': fitted_avm.feature_importances_,
                        'features_group': features_group,
                        }

    fitted_model = avm.fit(samples_train)
    predictions = avm.predict(samples_test)
    if predictions is None:
        print 'no predictions!'
        pdb.set_trace()
    actuals = samples_test[layout_transactions.price]
    return (
        ResultValue(actuals, predictions),
        make_importances(avm.model_name, fitted_model),
        )


def do_val(control, samples, save, already_exists):
    'run grid search on control.grid.hyperparameters across the 3 model kinds'

    def check_for_missing_predictions(result):
        for k, v in result.iteritems():
            if v.predictions is None:
                print k
                print 'found missing predictions'
                pdb.set_trace()

    def max_features_s(max_features):
        'convert to 4-character string (for printing)'
        return max_features[:4] if isinstance(max_features, str) else ('%4.1f' % max_features)

    def report(count, total, model_name):
        print 'fitting %d out of %d %s %s %s' % (
            count,
            total,
            model_name,
            control.arg.features_group,
            control.arg.hps,
            )

    result = {}

    def search_en(samples_test, samples_train):
        'search over ElasticNet HPs, appending to result'
        total = len(control.grid.units_X_seq)
        total *= len(control.grid.units_y_seq)
        total *= len(control.grid.alpha_seq)
        total *= len(control.grid.l1_ratio_seq)
        count = 0
        for units_X in control.grid.units_X_seq:
            for units_y in control.grid.units_y_seq:
                for alpha in control.grid.alpha_seq:
                    for l1_ratio in control.grid.l1_ratio_seq:
                        count += 1
                        report(count, total, 'en')
                        print (
                            control.arg.test_month,  'en', n_months_back, units_X[:3], units_y[:3],
                            alpha, l1_ratio,
                        )
                        avm = AVM.AVM(
                            model_name='ElasticNet',
                            random_state=control.random_seed,
                            units_X=units_X,
                            units_y=units_y,
                            alpha=alpha,
                            l1_ratio=l1_ratio,
                            features_group=control.arg.features_group,
                        )
                        result_key = ResultKeyEn(
                            n_months_back,
                            units_X,
                            units_y,
                            alpha,
                            l1_ratio,
                        )
                        if already_exists(result_key):
                            print 'already exists'
                        else:
                            print 'fitting and running', control.arg.features_hps_month, result_key
                            result_value = fit_and_run(
                                avm, samples_test, samples_train, control.arg.features_group,
                                )
                            save(result_key, result_value)
                            if control.arg.test:
                                return

    def search_gbr(samples_test, samples_train):
        'search over GradientBoostingRegressor HPs, appending to result'
        total = len(control.grid.n_estimators_seq)
        total *= len(control.grid.max_features_seq)
        total *= len(control.grid.max_depth_seq)
        total *= len(control.grid.loss_seq)
        total *= len(control.grid.learning_rate_seq)
        count = 0
        for n_estimators in control.grid.n_estimators_seq:
            for max_features in control.grid.max_features_seq:
                for max_depth in control.grid.max_depth_seq:
                    for loss in control.grid.loss_seq:
                        for learning_rate in control.grid.learning_rate_seq:
                            count += 1
                            report(count, total, 'gbr')
                            print (
                                control.arg.test_month, 'gbr', n_months_back,
                                n_estimators, max_features_s(max_features), max_depth, loss, learning_rate,
                            )
                            avm = AVM.AVM(
                                model_name='GradientBoostingRegressor',
                                random_state=control.random_seed,
                                learning_rate=learning_rate,
                                loss=loss,
                                alpha=.5 if loss == 'quantile' else None,
                                n_estimators=n_estimators,  # number of boosting stages
                                max_depth=max_depth,  # max depth of any tree
                                max_features=max_features,  # how many features to test whenBoosting splitting
                                features_group=control.arg.features_group,
                            )
                            result_key = ResultKeyGbr(
                                n_months_back,
                                n_estimators,
                                max_features,
                                max_depth,
                                loss,
                                learning_rate,
                            )
                            if already_exists(result_key):
                                print 'already exists'
                            else:
                                print 'fitting and running', result_key
                                result_value = fit_and_run(
                                        avm, samples_test, samples_train, control.arg.features_group,
                                        )
                                save(result_key, result_value)
                                if control.arg.test:
                                    return

    def search_rf(samples_test, samples_train):
        'search over RandomForestRegressor HPs, appending to result'
        total = len(control.grid.n_estimators_seq)
        total *= len(control.grid.max_features_seq)
        total *= len(control.grid.max_depth_seq)
        count = 0
        for n_estimators in control.grid.n_estimators_seq:
            for max_features in control.grid.max_features_seq:
                for max_depth in control.grid.max_depth_seq:
                    count += 1
                    report(count, total, 'rf')
                    print (
                        control.arg.test_month, 'rfr', n_months_back,
                        n_estimators, max_features_s(max_features), max_depth
                    )
                    avm = AVM.AVM(
                        model_name='RandomForestRegressor',
                        random_state=control.random_seed,
                        n_estimators=n_estimators,  # number of boosting stages
                        max_depth=max_depth,  # max depth of any tree
                        max_features=max_features,  # how many features to test when splitting
                        features_group=control.arg.features_group,
                    )
                    result_key = ResultKeyRfr(
                        n_months_back,
                        n_estimators,
                        max_features,
                        max_depth,
                    )
                    if already_exists(result_key):
                        print 'already exists'
                    else:
                        print 'fitting and running', result_key
                        result_value = fit_and_run(
                            avm, samples_test, samples_train, control.arg.features_group,
                            )
                        save(result_key, result_value)
                        if control.arg.test:
                            return

    # grid search for all model types
    for n_months_back in control.grid.n_months_back_seq:
        samples_test, samples_train = split_samples(samples, control.arg.test_month, n_months_back)

        search_en(samples_test, samples_train)
        search_gbr(samples_test, samples_train)
        search_rf(samples_test, samples_train)

    return result


class LocationSelector(object):
    def __init__(self, locality):
        locality_column_name = {
            'census': layout_transactions.census_tract,
            'city': layout_transactions.city,
            'global': None,
            'zip': layout_transactions.zip5,
            }[locality]
        self.locality_column_name = locality_column_name

    def location_values(self, df):
        'return values in the locality column'
        pdb.set_trace()
        values = df[self.locality_column_name]
        return values

    def in_location(self, df, location):
        'return samples that are in the location'
        pdb.set_trace()
        has_location = df[self.locality_column_name] == location
        subset = df.iloc[has_location]
        return subset


def make_model_name(result_key):
    if isinstance(result_key, ResultKeyEn):
        return 'ElasticNet'
    if isinstance(result_key, ResultKeyGbr):
        return 'GradientBoostingRegressor'
    if isinstance(result_key, ResultKeyRfr):
        return 'RandomForestRegressor'
    print 'unexpected result_key type', result_key, type(result_key)
    pdb.set_trace()


def fit_and_predict(samples, control, already_exists, save):
    'call save(ResultKey, ResultValue) for all the hps that do not exist'

    def split_test_train(n_months_back):
        '''return (test, train)
        where
        - test contains only transactions in the test_month
        - train contains only transactions in the n_months_back preceeding the
          test_month
        '''
        test_month = Month(control.arg.test_month)
        ss = SampleSelector(samples)
        samples_test = ss.in_month(test_month)
        samples_train = ss.between_months(
            test_month.decrement(n_months_back),
            test_month.decrement(1),
            )
        return samples_test, samples_train

    def make_avm(result_key):
        'return avm using specified hyperparameters'
        model_name = make_model_name(result_key)
        if model_name == 'ElasticNet':
            return AVM.AVM(
                model_name=model_name,
                random_state=control.random_seed,
                units_X=result_key.units_X,
                units_y=result_key.units_y,
                alpha=result_key.alpha,
                l1_ratio=result_key.l1_ratio,
                features_group=control.arg.features_group,
                )
        elif model_name == 'GradientBoostingRegressor':
            return AVM.AVM(
                model_name=model_name,
                random_state=control.random_seed,
                learning_rate=result_key.learning_rate,
                loss=result_key.loss,
                alpha=0.5 if result_key.loss == 'quantile' else None,
                n_estimators=result_key.n_estimators,
                max_depth=result_key.max_depth,
                max_features=result_key.max_features,
                features_group=control.arg.features_group,
                )
        elif model_name == 'RandomForestRegressor':
            return AVM.AVM(
                model_name=model_name,
                random_state=control.random_seed,
                n_estimators=result_key.n_estimators,
                max_depth=result_key.max_depth,
                max_features=result_key.max_features,
                features_group=control.arg.features_group,
                )
        else:
            print 'bad result_key.model_name', result_key
            pdb.set_trace()

    def make_importances(model_name, fitted_avm):
        if model_name == 'ElasticNet':
            return {
                    'intercept': fitted_avm.intercept_,
                    'coefficients': fitted_avm.coef_,
                    'features_group': control.arg.features_group,
                    }
        else:
            # the tree-based models have the same structure for their important features
            return {
                    'feature_importances': fitted_avm.feature_importances_,
                    'features_group': control.arg.features_group,
                    }

    def define_fit_predict_importances(test=None, train=None, hp=None):
        'return (ResultValue, importances)'
        assert test is not None
        assert train is not None
        assert hp is not None
        pdb.set_trace()
        avm = make_avm(hp)
        fitted_avm = avm.fit(train)
        predictions = avm.predict(test)
        actuals = test[layout_transactions.price]
        return ResultValue(actuals, predictions), make_importances(avm.model_name, fitted_avm)

    def make_result_value(result_key=None, samples_train=None, samples_validate=None):
        'return ResultValue'
        avm = make_avm(result_key)
        fitted_avm = avm.fit(samples_train)
        predictions = avm.predict(samples_validate)
        actuals = samples_validate[layout_transactions.price]
        importances = make_importances(avm.model_name, fitted_avm)
        return ResultValue(actuals=actuals, predictions=predictions), importances

    location_selector = LocationSelector(control.arg.locality)
    for result_key in make_result_keys(control):
        if already_exists(result_key):
            continue
        if control.debug and isinstance(result_key, ResultKeyEn):
            continue
        if control.debug and isinstance(result_key, ResultKeyGbr):
            continue
        all_samples_validate, all_samples_train = split_test_train(result_key.n_months_back)
        if control.arg.locality == 'global':
            # fit one model on all the training samples
            # use it to predict all the validation samples
            if control.debug:
                print 'global', result_key
            result_value, importances = make_result_value(
                result_key=result_key,
                samples_train=all_samples_train,
                samples_validate=all_samples_validate,
                )
            save(result_key, (result_value, importances))
        else:
            # fit one model for each location in the validation set (ex: city)
            # use it to predict just the validation samples in the same location
            pdb.set_trace()
            locations = location_selector.location_values(all_samples_validate)
            for location in set(locations):
                if control.debug:
                    print 'local', location, result_key
                pdb.set_trace()
                location_samples_validate = location_selector.in_location(all_samples_validate, location)
                location_samples_train = location_selector.in_location(all_samples_train, location)
                result_value, importances = make_result_value(
                    result_key=result_key,
                    samples_train=location_samples_train,
                    samples_validate=location_samples_validate,
                    )
                save(result_key, (result_value, importances))


FittedAvm = collections.namedtuple('FittedAVM', 'index key fitted')


def process_hps_best1(control, samples):
    'write files containing fitted models and feature names'
    # WRITEME: duplicate some functionality in do_val
    # get feature names from Features().ege_names(), which returns a tuple of strings
    def fit_and_write_k_best(best_models_f, k):
        with open(control.path_out_file, 'wb') as g:
            try:
                pickled = pickle.load(best_models_f)  # read until EOF or until K records are processed
                for index, key in enumerate(pickled):  # process the SortedDictionary
                    if index >= k:
                        # process only K best
                        break
                    print 'fitting index', index
                    avm = AVM.AVM(
                            model_name={
                                'en': 'ElasticNet',
                                'gb': 'GradientBoostingRegressor',
                                'rf': 'RandomForestRegressor',
                                }[key.model],
                            forecast_time_period=control.arg.test_month,
                            n_months_back=key.n_months_back,
                            random_state=control.random_seed,
                            verbose=True,
                            alpha=key.alpha,
                            l1_ratio=key.l1_ratio,
                            units_X=key.units_X,
                            units_y=key.units_y,
                            n_estimators=key.n_estimators,
                            max_depth=key.max_depth,
                            max_features=key.max_features,
                            learning_rate=key.learning_rate,
                            loss=key.loss,
                            features_group=control.arg.features_group,
                            )
                    samples_test, samples_train = split_samples(samples, control.arg.test_month, key.n_months_back)
                    fitted_value = fit_and_run(
                        avm,
                        samples_test,
                        samples_train,
                        control.arg.features_group,
                        )
                    record = (key, fitted_value)
                    pickle.dump(record, g)
            except EOFError:
                print 'found EOF for test_month:', control.arg.test_month

    path = control.path_in_best1
    print 'reading ranked model descriptions from', path
    with open(path, 'rb') as best_models_f:
        fit_and_write_k_best(best_models_f, 1)


def process_hps_all(control, samples):
    control.debug = True
    existing_keys_values = {}
    with open(control.path_out_file, 'rb') as prior:
        while True:
            try:
                record = pickle.load(prior)
                key, value = record
                existing_keys_values[key] = value
            except pickle.UnpicklingError as e:
                print key
                print e
                print 'ignored'
            except ValueError as e:
                print key
                print e
                print 'ignored'
            except EOFError:
                break
    print 'number of existing keys in output file:', len(existing_keys_values)
    control.timer.lap('read existing keys and values')

    # rewrite output file, staring with existing values
    with open(control.path_out_file, 'wb') as output:
        existing_keys = set(existing_keys_values.keys())

        def already_exists(key):
            return key in existing_keys

        def save(key, value):
            record = (key, value)
            pickle.dump(record, output)
            existing_keys.add(key)

        # write existing values
        for existing_key, existing_value in existing_keys_values.iteritems():
            if not control.debug:
                save(existing_key, existing_value)
        if control.debug:
            print 'since debugging, did not re-write output file'
        control.timer.lap('wrote new output file with existings key and values')
        existing_keys_values = None

        # write new values
        # do_val(control, samples, save, already_exists)
        fit_and_predict(samples, control, already_exists, save)
        control.timer.lap('create additional keys and values')


def main(argv):
    control = make_control(argv)
    if False:
        # avoid error in sklearn that requires flush to have no arguments
        sys.stdout = Logger(log_file_path=control.path_out_log)
    print control

    samples = pd.read_csv(
        control.path_in_samples,
        nrows=None if control.arg.test else None,
    )
    print 'samples.shape', samples.shape
    control.timer.lap('read samples')

    # assure output file exists
    if not os.path.exists(control.path_out_file):
        os.system('touch %s' % control.path_out_file)

    if control.arg.hps == 'all':
        process_hps_all(control, samples)
    else:
        process_hps_best1(control, samples)

    print control
    if control.arg.test:
        print 'DISCARD OUTPUT: test'
    if control.debug:
        print 'DISCARD OUTPUT: debug'
    print 'done'

    return


if __name__ == '__main__':
    if False:
        # avoid pyflakes warnings
        pdb.set_trace()
        pprint()
        pd.DataFrame()
        np.array()

    main(sys.argv)

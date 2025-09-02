#!/bin/bash

chemprop_predict --test_path uvvisml/data/splits/lambda_max_abs/deep4chem/group_by_smiles/smiles_target_test.csv --checkpoint_dir /Users/nathanleung/Documents/Programming/Research Projects/uvvisml/uvvisml/models/lambda_max_abs/chemprop/combined/production/fold_0 --preds_path test_preds.csv --number_of_molecules 2 --ensemble_variance
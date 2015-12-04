# --debug=basic
# disable built-in rules
.SUFFIXES:



PYTHON = ~/anaconda/bin/python

WORKING = ../data/working

ALL += $(WORKING)/census-features-derived.csv

# CHART02 and RFBOUND are obsoleted by RFVAL
# their rules and recipes are in rfbound.mk

GBRVAL += $(WORKING)/gbrval/200402.pickle
GBRVAL += $(WORKING)/gbrval/200405.pickle
GBRVAL += $(WORKING)/gbrval/200408.pickle
GBRVAL += $(WORKING)/gbrval/200411.pickle
GBRVAL += $(WORKING)/gbrval/200502.pickle
GBRVAL += $(WORKING)/gbrval/200505.pickle
GBRVAL += $(WORKING)/gbrval/200508.pickle
GBRVAL += $(WORKING)/gbrval/200511.pickle
GBRVAL += $(WORKING)/gbrval/200602.pickle
GBRVAL += $(WORKING)/gbrval/200605.pickle
GBRVAL += $(WORKING)/gbrval/200608.pickle
GBRVAL += $(WORKING)/gbrval/200611.pickle
GBRVAL += $(WORKING)/gbrval/200702.pickle
GBRVAL += $(WORKING)/gbrval/200705.pickle
GBRVAL += $(WORKING)/gbrval/200708.pickle
GBRVAL += $(WORKING)/gbrval/200711.pickle
GBRVAL += $(WORKING)/gbrval/200802.pickle
GBRVAL += $(WORKING)/gbrval/200805.pickle
GBRVAL += $(WORKING)/gbrval/200808.pickle
GBRVAL += $(WORKING)/gbrval/200811.pickle
GBRVAL += $(WORKING)/gbrval/200902.pickle
ALL += $(GBRVAL)

LINVAL += $(WORKING)/linval/200402.pickle
LINVAL += $(WORKING)/linval/200405.pickle
LINVAL += $(WORKING)/linval/200408.pickle
LINVAL += $(WORKING)/linval/200411.pickle
LINVAL += $(WORKING)/linval/200502.pickle
LINVAL += $(WORKING)/linval/200505.pickle
LINVAL += $(WORKING)/linval/200508.pickle
LINVAL += $(WORKING)/linval/200511.pickle
LINVAL += $(WORKING)/linval/200602.pickle
LINVAL += $(WORKING)/linval/200605.pickle
LINVAL += $(WORKING)/linval/200608.pickle
LINVAL += $(WORKING)/linval/200611.pickle
LINVAL += $(WORKING)/linval/200702.pickle
LINVAL += $(WORKING)/linval/200705.pickle
LINVAL += $(WORKING)/linval/200708.pickle
LINVAL += $(WORKING)/linval/200711.pickle
LINVAL += $(WORKING)/linval/200802.pickle
LINVAL += $(WORKING)/linval/200805.pickle
LINVAL += $(WORKING)/linval/200808.pickle
LINVAL += $(WORKING)/linval/200811.pickle
LINVAL += $(WORKING)/linval/200902.pickle
ALL += $(LINVAL)

RFVAL += $(WORKING)/rfval/200402.pickle
RFVAL += $(WORKING)/rfval/200405.pickle
RFVAL += $(WORKING)/rfval/200408.pickle
RFVAL += $(WORKING)/rfval/200411.pickle
RFVAL += $(WORKING)/rfval/200502.pickle
RFVAL += $(WORKING)/rfval/200505.pickle
RFVAL += $(WORKING)/rfval/200508.pickle
RFVAL += $(WORKING)/rfval/200511.pickle
RFVAL += $(WORKING)/rfval/200602.pickle
RFVAL += $(WORKING)/rfval/200605.pickle
RFVAL += $(WORKING)/rfval/200608.pickle
RFVAL += $(WORKING)/rfval/200611.pickle
RFVAL += $(WORKING)/rfval/200702.pickle
RFVAL += $(WORKING)/rfval/200705.pickle
RFVAL += $(WORKING)/rfval/200708.pickle
RFVAL += $(WORKING)/rfval/200711.pickle
RFVAL += $(WORKING)/rfval/200802.pickle
RFVAL += $(WORKING)/rfval/200805.pickle
RFVAL += $(WORKING)/rfval/200808.pickle
RFVAL += $(WORKING)/rfval/200811.pickle
RFVAL += $(WORKING)/rfval/200902.pickle
ALL += $(RFVAL)

CHARTS += $(WORKING)/chart-01/median-price.pdf
# use max_depth as a proxy for both max_depth and max_features
# use 2004-02 as a proxy for all years YYYY and months MM
CHARTS += $(WORKING)/chart-03/max_depth-2004-02.pdf
CHARTS += $(WORKING)/chart-04/2004-02.pdf

ALL += $(CHARTS)

ALL += $(WORKING)/parcels-features-census_tract.csv
ALL += $(WORKING)/parcels-features-zip5.csv

#ALL += $(WORKING)/samples-test.csv   # proxy for -train -train-test -train-train
#ALL += $(WORKING)/samples-train.csv   # proxy for -train -train-test -train-train
#ALL += $(WORKING)/samples-train-validate.csv   # proxy for -train -train-test -train-train
#ALL += $(WORKING)/samples-validate.csv   # proxy for -train -train-test -train-train

ALL += $(WORKING)/summarize-df-samples-train.csv
ALL += $(WORKING)/transactions-al-g-sfr.csv


.PHONY : all
all: $(ALL)

.PHONY : parcels-features
parcels-features: $(WORKING)/parcels-features-census_tract.csv $(WORKING)/parcels-features-zip5.csv

$(WORKING)/census-features-derived.csv: census-features.py layout_census.py
	$(PYTHON) census-features.py

# chart-01
$(WORKING)/chart-01/median-price.pdf: chart-01.py $(WORKING)/chart-01/data.pickle
	$(PYTHON) chart-01.py
	
$(WORKING)/chart-01/data.pickle: chart-01.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) chart-01.py --data

# chart-03
#    max_depth is a proxy for both max_depth and max_features
#    2004-02 is a proxy for all years YYYY and all months MM
CHART03REDUCTION = $(WORKING)/chart-03/data.pickle

$(CHART03REDUCTION): chart-03.py $(RFVAL)
	$(PYTHON) chart-03.py --data

$(WORKING)/chart-03/max_depth-2004-02.pdf: chart-03.py $(CHART03REDUCTION)
	$(PYTHON) chart-03.py 

# chart-04
CHART04REDUCTION = $(WORKING)/chart-04/data.pickle

$(CHART04REDUCTION): chart-04.py $(LINVAL)
	$(PYTHON) chart-04.py --data

$(WORKING)/chart-04/2004-02.pdf: chart-03.py $(CHART04REDUCTION)
	$(PYTHON) chart-04.py 

# gbrval
$(WORKING)/gbrval/200402.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200402

$(WORKING)/gbrval/200405.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200405

$(WORKING)/gbrval/200408.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200408

$(WORKING)/gbrval/200411.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200411

$(WORKING)/gbrval/200502.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200502

$(WORKING)/gbrval/200505.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200505

$(WORKING)/gbrval/200508.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200508

$(WORKING)/gbrval/200511.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200511

$(WORKING)/gbrval/200602.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200602

$(WORKING)/gbrval/200605.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200605

$(WORKING)/gbrval/200608.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200608

$(WORKING)/gbrval/200611.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200611

$(WORKING)/gbrval/200702.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200702

$(WORKING)/gbrval/200705.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200705

$(WORKING)/gbrval/200708.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200708

$(WORKING)/gbrval/200711.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200711

$(WORKING)/gbrval/200802.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200802

$(WORKING)/gbrval/200805.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200805

$(WORKING)/gbrval/200808.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200808

$(WORKING)/gbrval/200811.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200811

$(WORKING)/gbrval/200902.pickle: gbrval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) gbrval.py 200902

# linval
$(WORKING)/linval/200402.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200402

$(WORKING)/linval/200405.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200405

$(WORKING)/linval/200408.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200408

$(WORKING)/linval/200411.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200411

$(WORKING)/linval/200502.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200502

$(WORKING)/linval/200505.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200505

$(WORKING)/linval/200508.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200508

$(WORKING)/linval/200511.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200511

$(WORKING)/linval/200602.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200602

$(WORKING)/linval/200605.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200605

$(WORKING)/linval/200608.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200608

$(WORKING)/linval/200611.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200611

$(WORKING)/linval/200702.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200702

$(WORKING)/linval/200705.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200705

$(WORKING)/linval/200708.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200708

$(WORKING)/linval/200711.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200711

$(WORKING)/linval/200802.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200802

$(WORKING)/linval/200805.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200805

$(WORKING)/linval/200808.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200808

$(WORKING)/linval/200811.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200811

$(WORKING)/linval/200902.pickle: linval.py AVM_elastic_net.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) linval.py 200902

# rfval
$(WORKING)/rfval/200402.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200402

$(WORKING)/rfval/200405.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200405

$(WORKING)/rfval/200408.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200408

$(WORKING)/rfval/200411.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200411

$(WORKING)/rfval/200502.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200502

$(WORKING)/rfval/200505.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200505

$(WORKING)/rfval/200508.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200508

$(WORKING)/rfval/200511.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200511

$(WORKING)/rfval/200602.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200602

$(WORKING)/rfval/200605.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200605

$(WORKING)/rfval/200608.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200608

$(WORKING)/rfval/200611.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200611

$(WORKING)/rfval/200702.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200702

$(WORKING)/rfval/200705.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200705

$(WORKING)/rfval/200708.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200708

$(WORKING)/rfval/200711.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200711

$(WORKING)/rfval/200802.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200802

$(WORKING)/rfval/200805.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200805

$(WORKING)/rfval/200808.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200808

$(WORKING)/rfval/200811.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200811

$(WORKING)/rfval/200902.pickle: rfval.py AVM_random_forest_regressor.py $(WORKING)/samples-train-validate.csv
	$(PYTHON) rfval.py 200902

# parcels-*
$(WORKING)/parcels-features-census_tract.csv: parcels-features.py layout_parcels.py
	$(PYTHON) parcels-features.py --geo census_tract

$(WORKING)/parcels-features-zip5.csv: parcels-features.py layout_parcels.py
	$(PYTHON) parcels-features.py --geo zip5

$(WORKING)/transactions-al-g-sfr.csv: transactions.py \
	$(WORKING)/census-features-derived.csv \
	$(WORKING)/parcels-features-census_tract.csv $(WORKING)/parcels-features-zip5.csv 
	$(PYTHON) transactions.py

$(WORKING)/samples-test%csv $(WORKING)/samples-train%csv $(WORKING)/samples-train-validate%csv $(WORKING)/samples-validate%csv: samples.py $(WORKING)/transactions-al-g-sfr.csv
	$(PYTHON) samples.py

$(WORKING)/summarize-samples-train.csv: summarize-df.py summarize.py
	$(PYTHON) summarize-df.py --in samples-train.csv 

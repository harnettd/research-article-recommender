#!/bin/sh

# setup.sh - Harvest, process, and fit the data needed to run 
# the research-article recommender app.

DATADIR="data"
if ![ ! -d ${DATADIR} ];
    mkdir ${DATADIR}
fi
echo Collecting article data...
python src/get_data.py
echo ...done

echo Processing article data...
python src/make_dataset.py
echo ...done

MODELSDIR="models"
if ![ ! -d ${MODELSDIR} ];
    mkdir ${MODELSDIR}
fi
echo Fitting article data...
python src/fit_models.py
echo ...done

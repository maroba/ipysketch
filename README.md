# ipysketch

[![PyPI version](https://badge.fury.io/py/ipysketch.svg)](https://badge.fury.io/py/ipysketch)

A Python package for handwriting and sketching in Jupyter notebooks.

## Usage

#### A movie is worth a thousand pictures is worth a million words...

![Sketch Demo](res/demo.gif)

#### Where are my sketches saved?

When creating a `Sketch` instance, you give it a name, say *mysketch*. The sketch is then saved
in the same folder as the Jupyter notebook in two files with ending `.isk` and `.png`. The first file 
is the *ipysketch*-internal file format, the second is a PNG-representation of it, which is also 
displayed in the notebook. 

#### Using ipysketch without Jupyter

The *ipysketch* GUI can also be used outside of Jupyter notebooks. To create a sketch named
*mysketch* enter:

```
python -m ipysketch mysketch
```

## Installation

First, install the *ipysketch* package using *pip*:

```
pip install --upgrade ipysketch
```

Then install and enable the widgets extension in Jupyter:

```
jupyter nbextension install --user --py widgetsnbextension
jupyter nbextension enable --py widgetsnbextension
```

## Development

#### Set up development environment

Clone the repository

```
git clone https://github.com/maroba/ipysketch.git
```

Then install the package in development mode:

```
pip install -e .
```

#### Running the tests

```
python -m unittest discover test
```

### Running test coverage

If not already installed:

```
pip install coverage
```

Then 

```
coverage run --source=ipysketch setup.py test
coverage report -m
```

## Compatibility

*ipysketch* requires Python 3.


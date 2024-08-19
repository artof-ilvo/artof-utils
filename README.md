# ARTOF python utils

## Introduction

This python package is part of the [ARTOF](https://artof-ilvo.github.io) project and supports python add-ons.

## Usage

```bash
pip install artof-utils
```

## Build (No CI/CD)


1. Install the dependencies

```bash
pip install build
pip install twine
```

2. Build and publish the package

```bash
    python -m build
```

## Testing (No CI/CD)

1. Execute the following commands in the project root folder

```bash
export ILVO_PATH=tests/files/robot
coverage run -m pytest tests/test_*.py
```

## Licence

This project is under the ``ILVO LICENCE``.

```
Copyright (c) 2024 Flanders Research Institute for Agriculture, Fisheries and Food (ILVO)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

When the Software, including modifications and extensions, is used for:
- commercial or non-commercial machinery: the ILVO logo has to be clearly
   visible on the machine or on any promotion material which may be used in any
   agricultural fair or conference, in a way it is clear that ILVO contributed
   to the development of the software for the machine.
- a scientific or vulgarising publication: a reference to ILVO must be made as
   well as to the website of the living lab Agrifood Technology of ILVO:
   https://www.agrifoodtechnology.be

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
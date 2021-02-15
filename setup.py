import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="soso-uplot-jupyter-widget",
    version="0.0.1",
    author="Sohail Somani",
    author_email="me@sohailsomani.com",
    description="uPlot Jupyter Widget",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sohailsomani/soso-uplot_jupyter_widget",
    packages=['soso', 'soso.uplot_jupyter_widget'],
    namespace_packages=['soso'],
    package_test={
        'soso.uplot_jupyter_widget': ['*.pyi', 'py.typed'],
        'soso': ['*.pyi', 'py.typed']
    },
    install_requires=['jp_proxy_widget', 'ipywidgets', 'traitlets'],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ])

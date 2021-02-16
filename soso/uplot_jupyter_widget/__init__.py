import asyncio
import importlib.resources
import typing

import jp_proxy_widget
from traitlets import Bool, Dict, Int, List, Unicode

__all__ = ["uPlotWidget"]


class uPlotWidget(jp_proxy_widget.JSProxyWidget):  # type: ignore

    uplot_css = Unicode(
        "https://raw.githubusercontent.com/leeoniya/uPlot/master/dist/uPlot.min.css",  # noqa: E501
        allow_none=False)
    uplot_js = Unicode(
        "https://raw.githubusercontent.com/leeoniya/uPlot/master/dist/uPlot.iife.min.js",  # noqa: E501
        allow_none=False)

    # loaded after uPlot but before any other JS
    extra_js = List([])

    data = List([])
    # For options that expect a function, for example, DateFormatterFactory,
    # include the javascript as a string but prefix it with __js_eval. For
    # example: "opt": "__js_eval:() => console.log("HELLO")"
    opts = Dict({})

    max_datapoints = Int(None, allow_none=True)
    auto_resize = Bool(False, allow_none=False).tag(sync=True)

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super(uPlotWidget, self).__init__(*args, **kwargs)
        self.load_css(self.uplot_css)
        self.load_js_files([self.uplot_js])
        if self.extra_js:
            self.load_js_files(self.extra_js)

        self.__make_plot()

        self.observe(lambda: self.__make_plot(),
                     names=["data", "opts", "css", "js"])

    def __make_plot(self) -> None:
        js = importlib.resources.read_text(__package__, "js_init.include.js")
        self.js_init(js, data=self.data, opts=self.opts)

    def push_data(self, row: typing.List[float]) -> None:
        self.element.push_data(row, self.max_datapoints)

    def replace_data(self, data: typing.List[typing.List[float]]) -> None:
        if self.max_datapoints is not None:
            data = data[-self.max_datapoints:]
        self.element.replace_data(data)

    async def get_data_async(self) -> typing.List[typing.List[float]]:
        def cb(value: typing.List[typing.List[float]]) -> None:
            assert not fut.done()
            fut.set_result(value)

        fut: asyncio.Future[typing.List[typing.List[float]]] = asyncio.Future()
        self.get_value_async(cb, "element.__plot.data")
        await fut
        return fut.result()

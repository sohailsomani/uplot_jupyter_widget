import asyncio
import copy
import importlib.resources
import typing

import jp_proxy_widget
from ipywidgets import widgets  # type: ignore
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

    in_selection_mode = Bool(False).tag(sync=True)
    multiplier = Int(1).tag(sync=True)

    max_datapoints = Int(None, allow_none=True)
    auto_resize = Bool(False, allow_none=False).tag(sync=True)
    # Only used if auto_resize also true
    fullscreen = Bool(False, allow_none=False).tag(sync=True)

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super(uPlotWidget, self).__init__(*args, **kwargs)
        self._clicked = asyncio.Event()
        self._click_handlers = widgets.CallbackDispatcher()
        self.load_css(self.uplot_css)
        self.load_js_files([self.uplot_js])
        if self.extra_js:
            self.load_js_files(self.extra_js)

        self.__make_plot()

        self.observe(lambda _: self.__make_plot(),
                     names=["data", "opts", "css", "js", "max_datapoints", "multiplier"])

    def handle_custom_message_wrapper(self, widget: typing.Any, data: typing.Dict[str, typing.Any],
                                      *etcetera: typing.Any) -> None:
        if data.get('event', '') == 'click':
            d = data.copy()
            del d['event']
            self._click_handlers(d)
        else:
            super().handle_custom_message_wrapper(widget, data, *etcetera)

    def on_click(self,
                 callback: typing.Callable[[typing.Dict[str, float]], None],
                 remove: bool = False) -> None:
        self._click_handlers.register_callback(callback, remove=remove)

    async def select_point(self) -> typing.Dict[str, float]:
        self.in_selection_mode = True
        try:
            out = []
            self._clicked.clear()

            def callback(d: typing.Dict[str, float]) -> None:
                for key in d.keys():
                    if d[key]:
                        d[key] = d[key] / float(self.multiplier)
                out.append(d)
                self._clicked.set()

            self.on_click(callback, remove=False)
            await self._clicked.wait()
            self.on_click(callback, remove=True)
            return out[0]
        finally:
            self.in_selection_mode = False

    def __slice_data(self,
                     data: typing.List[typing.List[float]]) -> typing.List[typing.List[float]]:
        data = copy.deepcopy(self.data)
        if self.max_datapoints is not None:
            for idx in range(len(data)):
                data[idx] = data[idx][-self.max_datapoints:]
        for d in data[1:]:
            for i in range(len(d)):
                if d[i]:
                    d[i] = d[i] * self.multiplier
        return data

    def __make_plot(self) -> None:
        js = importlib.resources.read_text(__package__, "js_init.include.js")
        data = self.__slice_data(self.data)
        self.js_init(js, data=data, opts=self.opts)

    def push_data(self, row: typing.List[typing.Optional[float]]) -> None:
        row = [row[0]] + [self.multiplier * r if r else r for r in row[1:]]
        msg: typing.Dict[str, typing.Any] = {
            'command': '__uplot_push_data',
            'payload': [row, self.max_datapoints]
        }
        self.send(msg)

    def replace_data(self, data: typing.List[typing.List[float]]) -> None:
        data = self.__slice_data(data)
        self.element.replace_data(data)

    async def get_data_async(self) -> typing.List[typing.List[float]]:
        def cb(value: typing.List[typing.List[float]]) -> None:
            assert not fut.done()
            fut.set_result(value)

        fut: asyncio.Future[typing.List[typing.List[float]]] = asyncio.Future()
        self.get_value_async(cb, "element.__plot.data")
        await fut
        return fut.result()

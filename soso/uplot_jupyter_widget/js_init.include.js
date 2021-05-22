// Note: this code expects to be executed in js_init
// Also this code is ugly and gross.
const __jseval_recursive = (obj) => {
    __eval_recursive = (obj,key) => {
        const value = obj[key];
        if((typeof value == "string") && value.startsWith("__js_eval:")) {
            obj[key] = eval(value.replace("__js_eval:",""));
        } else if (value.constructor == Object){
            __jseval_recursive(value);
        } else if (Array.isArray(value)) {
            for(let key in value) {
                __eval_recursive(value,key);
            }
        }
    };
    for(let key in obj) {
        __eval_recursive(obj,key);
    }
};

this.el.innerHTML = '';
__jseval_recursive(opts);

for(let ii = 0; ii < data.length; ++ii) {
    for(let jj=0; jj < data[ii].length; ++jj) {
        if(isNaN(data[ii][jj])) {
            data[ii][jj] = null;
        }
    }
}

let plot = new uPlot(opts,data,this.el);
element.__plot = plot;

element.replace_data = (rows) => {
    plot.setData(rows,true);
    __update_size();
};

let __batched_rows = [];

let __do_actual_push_data = () => {
    let rows = __batched_rows;
    __batched_rows = [];
    let max_data = this.model.get('max_data');
    let data = plot.data.slice(0);
    let last_x = data[0][data[0].length-1];
    for(let rr = 0; rr < rows.length; ++rr) {
        let row = rows[rr];
        let newTimepoint = false;
        let ii;
        // if the time point is the same
        if(row[0] == data[0][data[0].length-1]) {
            // just update the last row
            for(ii = 0; ii < row.length; ++ii) {
                data[ii][data[ii].length-1] = row[ii];
            }
        } else { // new timepoint
            for(ii = 0; ii < row.length; ++ii) {
                data[ii].push(row[ii]);
            }
        }
        if (typeof(max_data) == 'number') {
            for(ii =0; ii < row.length; ++ii) {
                if(data[ii].length < max_data) continue;
                data[ii] = data[ii].slice(-max_data);
            }
        }
        for(ii = 0 ;ii < data.length; ++ii) {
            if(isNaN(data[ii][data[ii].length-1])) {
                data[ii][data[ii].length-1] = null;
            }
        }
    }
    // Don't redraw anything if we have a selection or we got a new x value
    const [xmin, xmax] = [plot.scales.x.min, plot.scales.x.max];
    const rescaleAxes = xmin == 0 && xmax == (plot.data[0].length-1);
    const newX = last_x != data[0][data[0].length-1];
    plot.setData(data, newX || rescaleAxes);
};

this.__interval = null;

let __push_data = (row,max_data) => {
    if(!this.__interval) {
        this.__interval = setInterval(() => {
            if(__batched_rows.length > 0) {
                requestAnimationFrame(__do_actual_push_data);
            } else {
                clearInterval(this.__interval);
                this.__interval = null;
            }
        },100);
    };
    __batched_rows.push(row);
};

const self = this;
// overwrite jp_proxy_widget message handling
// because protocol is too chatty otherwise for quick updates.
const old_handle_custom_message = self.handle_custom_message.bind(self);
self['handle_custom_message'] = function(content,buffers,widget) {
    if(content['command'] == '__uplot_push_data') {
        const row = content['payload'][0];
        const max_data = content['payload'][1];
        __push_data(row,max_data);
    } else {
        old_handle_custom_message(content,buffers,widget);
    }
};

if(this.el.hasOwnProperty('_handle_click')) {
    this.el.removeEventListener('click',this.el._handle_click);
}

this.el._handle_click = (event) => {
    const {left,top} = plot.cursor;
    data = {
        event: 'click'
    };
    // true = canvas coordinates
    data[plot.series[0].scale] = plot.posToVal(left,plot.series[0].scale,true);
    for(let ii = 1; ii < plot.series.length; ++ii) {
        const s = plot.series[ii];
        data[s.scale] = plot.posToVal(top,s.scale,true);
    }
    this.send(data);
};

this.el.addEventListener('click',this.el._handle_click);

this.model.on('change:in_selection_mode',() => {
    this.el.classList.toggle('uplot-in-selection-mode',this.model.get('in_selection_mode'));
});

__update_size = () => {
    const auto_resize = this.model.get('auto_resize');
    if(!auto_resize) return;
    const fullscreen = this.model.get('fullscreen');

    const element = this.el;
    const title = this.el.querySelector(".u-title");
    const legend = this.el.querySelector(".u-legend");

    const titleHeight = !!title ? title.clientHeight : 0;
    const legendHeight = !!legend ? legend.clientHeight : 0;

    let height, width;
    if(fullscreen) {
        height = window.innerHeight - 100 - titleHeight - legendHeight;
        width = element.clientWidth; // probably wrong
        if(!!this.el.parentElement) {
            this.el.parentElement.style.height = height + 'px';
            this.el.parentElement.style.padding = "0px";
        }
    } else {
        height = element.clientHeight - titleHeight - legendHeight; // # noqa
        width = element.clientWidth;
    }

    if (isNaN(height) || isNaN(width)) return;
    plot.setSize({
        height: height,
        width: width
    });
};

// https://davidwalsh.name/javascript-debounce-function
function __debounce(func, wait, immediate) {
    let timeout;
    return function() {
        let context = this, args = arguments;
        let later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        let callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
};

const __debounced_resize = __debounce(__update_size,250);

// Initial resize
setTimeout(__update_size,1000);

this.el.addEventListener("resize",__debounced_resize);
window.addEventListener("resize",__debounced_resize);

console.log("uplot_jupyter_widget:js_init done",element);

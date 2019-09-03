/* @flow */
import {unwrap} from './common';
import {get_options_async, setOptions} from './options';
import {defensifyAlert, alertError} from './notifications';

// $FlowFixMe
import reqwest from 'reqwest';

// $FlowFixMe
import CodeMirror from 'codemirror/lib/codemirror.js';
// $FlowFixMe
import 'codemirror/mode/css/css.js';
// err. that's a bit stupid, js injected css? surely it can be done via webpacke and static files...
// $FlowFixMe
import 'codemirror/lib/codemirror.css';
// turned out more tedious than expected... https://github.com/codemirror/CodeMirror/issues/5484#issue-338185331


function getInputElement(element_id: string): HTMLInputElement {
    return ((document.getElementById(element_id): any): HTMLInputElement);
}

function getElement(element_id: string): HTMLElement {
    return ((document.getElementById(element_id): any): HTMLElement);
}

function getHost(): HTMLInputElement {
    return getInputElement('host_id');
}

function getToken(): HTMLInputElement {
    return getInputElement('token_id');
}

// function getDots(): HTMLInputElement {
//     return getInputElement('dots_id');
// }

function getBlackList(): HTMLInputElement {
    return getInputElement('blacklist_id');
}

function getSrcMap(): HTMLInputElement {
    return getInputElement('source_map_id');
}

function getPositionCss(): HTMLElement {
    return getElement('position_css_id');
}

function getExtraCss(): HTMLElement {
    return getElement('extra_css_id');
}

// TODO display it floating

function getExtraCssEditor() {
    // $FlowFixMe
    return getExtraCss().querySelector('.CodeMirror').CodeMirror;
}


function getPositionCssEditor() {
    // $FlowFixMe
    return getPositionCss().querySelector('.CodeMirror').CodeMirror;
}


document.addEventListener('DOMContentLoaded', defensifyAlert(async () => {
    const opts = await get_options_async();
    getHost().value      = opts.host;
    getToken().value     = opts.token;

    // getDots().checked    = opts.dots;
    getBlackList().value = opts.blacklist;
    // TODO tag map could be json?
    getSrcMap().value    = JSON.stringify(opts.src_map);

    CodeMirror(getPositionCss(), {
        mode       : 'css',
        lineNumbers: true,
        value      : opts.position_css,
    });

    CodeMirror(getExtraCss(), {
        mode       :  'css',
        lineNumbers: true,
        value      : opts.extra_css,
    });
}));

unwrap(document.getElementById('backend_status_id')).addEventListener('click', defensifyAlert(async() => {
    const host = getHost().value;
    const token = getToken().value;

    await reqwest({
        url: `${host}/status`,
        method: 'post',
        headers: {
            'Authorization': "Basic " + btoa(token),
        },
        timeout: 1000, // 1s
    }).then(res => {
        console.log(res);
        alert(`Success! ${JSON.stringify(res)}`);
    }, err => {
        // TODO ugh. unclear how to transform error object, nothing seemed to work.
        // that results in two error alerts, but I guess thats' not so bad..
        alertError(`${err.status} ${err.statusText} ${err.response}`);
    });
}));

// TODO careful here if I ever implement not showing notifications?
// defensify might need to alert then...
unwrap(document.getElementById('save_id')).addEventListener('click', defensifyAlert(async () => {
    // TODO make opts active object so we don't query unnecessary things like blacklist every time?
    const opts = {
        host      : getHost().value,
        token     : getToken().value,

        dots      : true, // TODO? getDots().checked,
        blacklist : getBlackList().value,
        src_map   : JSON.parse(getSrcMap().value),

        position_css : getPositionCssEditor().getValue(),
        extra_css    : getExtraCssEditor().getValue(),
    };
    await setOptions(opts);
    alert("Saved!");
}));

/**
 * Created by pbpoo_000 on 2017/6/13.
 */
Vue.config.delimiters = ["[[", "]]"]

var app = new Vue({
    el: '#app',
    data: {
        'formset': '{{ formset|safe }}',
    },
});
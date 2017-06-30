/**
 * Created by pbpoo on 2017/6/30.
 */

// 以下是slab_list的js代码

function select_all(id, vall) {
    // 全选或全不选
    var sid = id.split('_').slice(0, 1).join('_');

    $("#" + sid + " table :checkbox").each(function () {
        $(this).prop("checked", vall);
    });
    sum_m2(watch_select());
}
;

function select_reverse(id) {
    // 反选
    var sid = id.split('_').slice(0, 1).join('_');
    console.log(sid)
    $("#" + sid + " table :checkbox").each(function () {
        $(this).prop("checked", !this.checked);
    });
    sum_m2(watch_select());
}

function watch_select() {
    var all_sid = new Array();
    $("table :checkbox").each(function () {
        if (this.checked) {
            all_sid.push($(this).val())
        }
    });
    return all_sid
};

function sum_m2(sid_list) {
    var sum = 0;
    for (var i in sid_list) {
        var m2 = new Number($('#' + sid_list[i] + 'm2').text());
        console.log(m2)
        sum += m2;
    }
    select_info(sid_list.length, sum)
}

function select_info(pics, m2) {
    $("#selected_info li[name=pics] b").text(pics);
    $("#selected_info li[name=m2] b").text(m2.toFixed(2));
}
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
        sum += m2;
    }
    select_info(sid_list.length, sum)
}

function select_info(pics, m2) {
    $("#selected_info li[name=pics] b").text(pics);
    $("#selected_info li[name=m2] b").text(m2.toFixed(2));
}
//获取datalist数据
function get_source(id) {
    console.log(id);
    var block_num_id = id.split('_').splice(0, 2).join('_') + '_num';
    console.log(block_num_id); //block_num_id input框的id
    var value = $('#' + id).val(); //输入的荒料编号
    console.log(value);
    var select = $('#block_info').find('option[value="' + value + '"]')
    //荒料对应的id
    console.log(select.data('id'));

    if (!select.data('id')) {
        alert('荒料编号[' + value + '],不是本订单内容合法的编号，请检查！')
        setfocus(id)
    } else {
        $('#' + block_num_id).val(select.data('id'))
    }
    set_quantity(id, select)
}
;

function setfocus(id) {
    $('#' + id).focus()
}
//界石订单选择编号后设置重量
function set_quantity(id, se) {
    var order_type = $('#order_type').val()
    console.log(order_type)
    if (order_type == 'KS') {
        console.log(id)
        var quantity = id.split('-').splice(0, 2).join('-') + '-quantity';
        console.log(quantity)
        $('#' + quantity).val(se.data('quantity'))
    }
}

//formset添加form，一定要在table的id改为formset

function add_form(prefix) {

    // var prefix = formsetprefix;
    var new_form = $('#formset tbody tr:last').clone(true);
    var total_count = $('#id_' + prefix + '-TOTAL_FORMS').val();
    new_form.find(':input').each(function () {
        // var count = $(this).attr('name').split('-').slice(1, 2)
        // var c = count[0]
        // console.log(c)
        var name = $(this).attr('name').replace('-' + (total_count - 1) + '-', '-' + (total_count) + '-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id}).val('').remove('checked');
    });
    // new_form.find('td:last').html('<button class="btn btn-danger" type="button" name="remove_button" value="' + prefix + '" id="remove_' + total_count + '" onclick="remove_form(this.id)">删除</button>');
    total_count++
    $('#id_' + prefix + '-TOTAL_FORMS').val(total_count);
    $('#formset tbody tr:last').after(new_form);
}
;
//删除一行数据
function remove_form(prefix) {
    // var prefix = $('#' + id).val()
    var total_count = $('#id_' + prefix + '-TOTAL_FORMS').val();
    if (total_count >= 2) {
        $('#formset tbody tr:last').remove();
        total_count--;
        $('#id_' + prefix + '-TOTAL_FORMS').val(total_count);
        // $('#' + id).parent('td').parent('tr').remove();
    }

};

function open_dt(id) {
    $('#' + id).datetimepicker({
        minView: "day", //  选择时间时，最小可以选择到那层；默认是‘hour’也可用0表示
        language: 'zh-CN', // 语言
        autoclose: true, //  true:选择时间后窗口自动关闭
        format: 'yyyy-mm-dd ', /* 文本框时间格式，设置为0,最后时间格式为2017-03-23 17:00:00
         //hh:00:00*/
        todayBtn: 'linked', /* 如果此值为true 或 "linked"，则在日期时间选择器组件的底部显示一个 "Today"
         按钮用以选择当前日期。*/
    })
}
function open_slab_list(id, url) {
    console.log(id)
    var select_id = id.split('-').slice(0, 2).join('-');
    var block_num = $('#' + select_id + '-block_name').val();
    var thickness = $('#' + select_id + '-thickness').val();
    gogo_slab_list(block_num, thickness, url)
}

function gogo_slab_list(block_num, thickness, url) {
    // var slab_ids = ids
    console.log(url)
    console.log(block_num, thickness)
    // var thickness =thickness
    // var block_num = block_num
    var _url = url + "?block_num=" + block_num + "&thickness=" + thickness;
    //以后要在JavaScript里使用django的url连接需要用这个方式连接字符串
    var w_width = window.innerWidth / 2 - 250
    var slab_window = window.open(_url, "new", "menubar=yes,width=500,height=700 ", "resizeable=yes");
    var slab_top = screen.width / 2 - 250
    var slab_left = screen.height / 2 - 700
    slab_window.moveTo(slab_top, slab_left)
    // timer = window.setInterval("IfWindowClosed()", 500);
}
// var timer
// var slab_window
// function IfWindowClosed() {
//     //判断子窗体是否关闭
//     if (slab_window.closed == true) {
//         alert("close");
//         window.clearInterval(timer);
//         slab_window.location.reload()
//     }
// }


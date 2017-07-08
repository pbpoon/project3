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
//获取datalist数据
function get_source(id) {
    console.log(id);
    var block_num_id = id.split('_').splice(0, 2).join('_') + '_num';
    console.log(block_num_id); //block_num_id input框的id
    var value = $('#' + id).val(); //输入的荒料编号
    console.log(value);
    var select = $('#block_info').find('option[value="' + value + '"]').data('id')
    //荒料对应的id
    console.log(select.data('id'));
    if (!select_id) {
        alert('荒料编号['+value+'],不是本订单内容合法的编号，请检查！')
        setfocus(id)
    }else{
        $('#' + block_num_id).val(select.data('id'))
    }
    set_quantity(id,select)
}
;

function setfocus(id) {
    $('#'+id).focus()
}

function set_quantity(id,se) {
    var order_type= $(':input[name=order_type]').val()
    console.log(order_type)
    if(order_type=='KS'){
        var quantity = id.split('_').splice(0, 2).join('_') + '_quantity';
        console.log(quantity)
        quantity.val(se.data('quantity'))
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

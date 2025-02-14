function applySeat() {
    var num = Number($("#sum").text());
    if (num > 0) {
        if ($("#cr").length > 0) {
            if (!$("#cr").is(":checked")) {
                info('请阅读说明后预订！');
                return false;
            }
        }
        
        loadding();
        // loadInfo("锁定座位", "正在为您锁定座位.....请勿刷新页面！");
        var model = {};

        var stock = {};
        var seatid = [];
        $('#seatshow').find('.ticket-auto').each(function (i, k) {
            seatid.push($(k).attr('data-did'));
            stock[$(k).attr('data-stockid')] = (stock[$(k).attr('data-stockid')] == null ? 1 : Number(stock[$(k).attr('data-stockid')]) + 1) + '';
        })
        model.stock = stock;
        model.istimes = '1';
        model.address = $('#serviceid').val();
        model.stockdetailids = seatid.join(',');

        var param = {};
        param.serviceid = $('#serviceid').val();
        param.num = seatid.length;
        param.date = $('.date-week').find('li.active').attr('data');
        //AjaxGet('/order/booklimt',param,function(o){
        //	if(o.result == 1){
        //		$('#param').val(JSON.stringify(model));
        //		$('#form1').submit();
        //	}else{
        //		info(o.message);
        //	}
        //},'json');

        $('#param').val(JSON.stringify(model));
        $('#form1').submit();

        // alert(JSON.stringify(model));

    } else {
        info("请选择需要预订的" + typename + "信息！");
    }

}
function createOrder(yzm) {
	goonreserve(yzm);
}

function goonreserve(yzm) {

	if (yzm == '' || typeof (yzm) == 'undefined') {
		yzmWindow();
		return false;
	}
	if (_param != 'undefined') {
		loadding();
		if (set_iphone == 1) {
			if ($('#remark').val() == null || $('#remark').val() == '') {
				info('请填写手机号码');
				return false;
			}
			if (!phone.test($("#remark").val())) {
				info("请输入有效的手机号码");
				return false;
			}
			_param.remark = $('#remark').val();
		}

		var param1 = {};
		param1.param = JSON.stringify(_param);
		closeed();
		param1.yzm = yzm;
		AjaxPost('/order/book', param1, function (o) {

			loadding();
			if (o.result != null) {
				if (o.result == '1') {
					loadding();
					window.location.href = cu('/order/myorder_view') + '?id=' + o.object.orderid;
				} else if (o.result == '2') {
					warning1("现在去支付？", "topaypage", "no", o.object.orderid, o.object.orderid);
				} else {
					info(o.message);
				}
			}

		});
	} else {
		error('数据有误，请返回重试');
	}
}

function yzmWindow() {
	loaddingWhite();
	$('#captcha-iframe').show();
}

function loaddingWhite() {
	var loaddinghtml = '<div class="bodymask-loader fade in" style="background-color:#fff;opacity:0.8;"><iframe id="captcha-iframe" class="captcha-iframe" src="/yzm/slider.html"></div><div class="loader text-center"><div class="loader-inner pacman"><div></div><div></div><div></div><div></div><div></div></div></div>';
	$("body").append(loaddinghtml);
}
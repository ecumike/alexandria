////////////////////////
//	Core namespace util.
////////////////////////
AL.namespace = function() {
	var scope = arguments[0],
		ln = arguments.length,
		i, value, split, x, xln, parts, object;

	for (i = 1; i < ln; i++) {
		value = arguments[i];
		parts = value.split(".");
		object = scope[parts[0]] = Object(scope[parts[0]]);
		for (x = 1, xln = parts.length; x < xln; x++) {
			object = object[parts[x]] = Object(object[parts[x]]);
		}
	}
	return object;
};



(function($){
	
	
	function setupDynamicFields () {
		$("[data-widget='dynamic-fields']").each(function () {
			var $widgetCon = $(this);
			
			$widgetCon.on('click', 'a', function (evt) {
				evt.preventDefault();
				
				if (this.classList.contains('dynamic-fields-remove')) {
					if ($widgetCon.find('.dynamic-fields-item').length > 1) {
						$(this).closest('.dynamic-fields-item').slideUp(function(){$(this).closest('.dynamic-fields-item').remove()});
					}
					else {
						$(this).closest('.dynamic-fields-item').find('input').val('');
					}
				}
				else if (this.classList.contains('dynamic-fields-add')) {
					var $newitem = $widgetCon.find('.dynamic-fields-item').last().clone().css({'display':'none'});
					$newitem.find('input, textarea').removeAttr('id').val('');
					$newitem.insertAfter($widgetCon.find('.dynamic-fields-item').last()).slideDown(function () {
						$newitem.find('input, textarea').focus();
					});	
				}
			});
		});
	}
	
	
	function flashMessage (el) {
		el.classList.add('bl-fadein');
		setTimeout(function () {
			el.classList.remove('bl-fadeout');
		}, 10);
		setTimeout(function () {
			el.classList.add('bl-fadeout');
		}, 1600);	
	}
	AL.flashMessage = flashMessage;
	
	
	function enableHotlinkrows () {
		setTimeout(function () {
			BO.hotlinkRows($("[data-widget='datatable']"));
		}, 1000);
	}
	AL.enableHotlinkrows = enableHotlinkrows;
	
	
	$(function () {
		setupDynamicFields();
	});
	
	
	
})(jQuery);




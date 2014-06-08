(function($){
    var defaults = {
	'refresh' : '2000',
	'readBytes' : 65535
    }

    var serialLogger = function (){
	headReq = function(){
	    $.ajax({type: "HEAD",
		    url: serialLogger.options.logURL,
		    cache: false,
		    complete: function(xhr, status) {
			if((status == "complete" || status == "nocontent") && xhr.status == 200)
			    update(parseInt(xhr.getResponseHeader("Content-Length")));
		    }
		   });
	},
	update = function (newLength){
	    if(serialLogger.length < newLength) 
	    {
		var sRange = serialLogger.length;
		var readBytes = parseInt(serialLogger.options.readBytes);
		
		if (serialLogger.length == 0 && newLength > readBytes)
		    sRange = newLength - readBytes;
		else if (serialLogger.length > 0)
		    sRange--;
		
		$.ajax({
		    type: "GET",
		    url: serialLogger.options.logURL,
		    cache: false,
		    dataType:"text",
		    beforeSend: function(http){
			http.setRequestHeader('Range', 'bytes='+sRange+'-');
		    },
		    success: function(d) {
			$("#" + serialLogger.options.targetObjectID).append(cleanTags(d));
			var el = document.getElementById(serialLogger.options.targetObjectID);
			el.scrollTop = el.scrollHeight;  
		    }
		});
		serialLogger.length = newLength; 
	    }
	    else if(serialLogger.length > newLength) // we assume the log changed or got deleted with this step
	    {
		serialLogger.length = 0;
		$("#" + serialLogger.options.targetObjectID).html('\nThe log has rolled...\n\n');
	    }
	    setTimeOut();
	},
	setTimeOut = function(){
	    if (serialLogger.timeoutID > 0) {
		window.clearTimeout(serialLogger.timeoutID);
	    }
	    serialLogger.timeoutID = window.setTimeout(headReq, serialLogger.options.refresh);
	},
	cleanTags = function(html){
	    return html.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
	};
        
	return {
	    init: function(options) {
		if (options.logURL == undefined ) 
		{
		    console.warn('No specified url');
		    return false;
		}
		
		options.targetObjectID = $(this).attr('id');
		serialLogger.options = $.extend({},defaults,options);
		serialLogger.length = 0;
                serialLogger.length = 0;
		headReq();
	    }
	};
    }();

    $.fn.extend({
	serialLogger: serialLogger.init
    });

})($)
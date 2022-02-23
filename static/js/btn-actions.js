$(".conf-delete").click(function(){
    var id = $(this).data('id');
    bootbox.confirm("Are you sure?", function(result) {
      if(result)
          window.location = '/jobs/delete/' + id;
    });
  });

$(".conf-heat").click(function(){
    bootbox.alert({
    message: "Printers heating!",
    size: 'small',
    backdrop: true
    });
});
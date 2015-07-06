$(function () {
  $(".vote").click(function (e) {
    var sel = $(this);
    var obj = sel[0];
    sel.toggleClass('enabled');
    if (obj.dataset.dir == "up")
      sel.siblings(".down").removeClass('enabled');
    else
      sel.siblings(".up").removeClass('enabled');
    $.ajax({
      url: "/api/vote/" + obj.dataset.type + "/" + obj.dataset.group + "/" + obj.dataset.id + "/" + obj.dataset.dir,
    });
  });
});

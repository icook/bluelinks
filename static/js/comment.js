$(function () {
  var submission = function(sel) {
    var obj = sel[0];
    $.ajax({
        method: "POST",
        dataType: "json",
        url: "/api/post_comment/" + obj.dataset.parent,
        data: sel.serializeObject()
    });
  }
  $("#comment-submit").click(function (e) {
      submission($(this).parents('form'));
  });
});

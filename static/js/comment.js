$(function () {
  var submission = function(sel) {
    var obj = sel[0];
    var data = sel.serializeObject();
    data['post_id'] = post_id;
    $.ajax({
        method: "POST",
        dataType: "json",
        url: "/api/post_comment/" + obj.dataset.parent,
        data: data
    });
  }
  $("#comment-submit").click(function (e) {
      submission($(this).parents('form'));
  });
});

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
  };
  $("[name=submit]").click(function (e) {
    submission($(this).parents('form'));
    location.reload();
  });
  $(".reply-link").click(function (e) {
    var t = $(this);
    var div = t.parent().children('.comment-reply');
    var form = $("#comment-form").clone().attr("data-parent", this.dataset.parent);
    form.find('[name=submit]').click(function (e) {
      submission($(this).parents('form'));
    });
    div.html(form);
  });
});

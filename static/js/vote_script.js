$(function () {
  $(".vote").click(function (e) {
    var sel = $(this);
    var obj = sel[0];
    var direction = obj.dataset.dir;
    var up = obj.dataset.dir == "up";
    var change = 0;
    if (sel.toggleClass('enabled').hasClass('enabled')) {
        // Only run if we aren't removing the vote
        change += up ? 1 : -1;
        if (up) {
            if (sel.siblings(".down").hasClass('enabled')) {
                sel.siblings(".down").removeClass('enabled');
                change += 1;
            }
        } else {
            if (sel.siblings(".up").hasClass('enabled')) {
                sel.siblings(".up").removeClass('enabled');
                change -= 1;
            }
        }
    } else {
        change += up ? -1 : 1;
        direction = "remove";
    }
    display_score = parseInt(sel.siblings('.score').html());
    display_score += change;
    sel.siblings('.score').html(display_score);
    $.ajax({
      url: "/api/vote/" + obj.dataset.type + "/" + obj.dataset.group + "/" + obj.dataset.id + "/" + direction,
    });
  });
});

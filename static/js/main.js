$(function () {
  window.helpers = {
    message: function(message, classes) {
      var id = Math.random().toString(36).substr(2, 5);
      var obj = $(["<div class='", classes, "' id='", id, "'>",
        message,
        "</div>"].join(""));
      obj.appendTo('#alertbox').hide().fadeIn(600);
      setTimeout(function() {
        $("#" + id).fadeOut(600, function() { $(this).remove(); });
      }, 2000);
    },
    success: function(message) {
      this.message(message, "alert alert-success");
    },
    warning: function(message) {
      this.message(message, "alert alert-warning");
    },
    error: function(message) {
      this.message(message, "alert alert-danger");
    },
    validate_email: function validEmail(v) {
      var r = new RegExp("[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?");
      return (v.match(r) != null);
    },
    confirm: function(modal_id, confirm_id, confirm_callback) {
      $(confirm_id).unbind('click');
      $(confirm_id).on('click', function(event) {
        event.preventDefault();
        $(modal_id).modal('hide');
        confirm_callback();
      });
      $(modal_id).modal('show');
    },
    ajax_check: function(url, success_callback, fail_callback) {
        $.ajax({
          dataType: "json",
          method: "GET",
          url: url
        }).done(function (data) {
          success_callback(data);
        }).fail(function (jqXHR, textStatus, errorThrown) {
          fail_callback(jqXHR);
        });
    },
    ajax_save: function(url, data, spinner_id, success_callback,
                             fail_callback) {
      var spinner = $('#' + spinner_id);
      spinner.fadeIn(200, function () {
        $.ajax({
          dataType: "json",
          method: "POST",
          url: url,
          data: data
        }).done(function (data) {
            var animation_finished = function() { success_callback(data); };
            spinner.fadeOut(200, animation_finished);
        }).fail(function () {
          spinner.fadeOut(400, fail_callback);
        });
      });
    },
    upload_s3: function(upload_button_id) {
      var upload_button = $('#' + upload_button_id);
      var prod_id = upload_button.data('prod-id');
      var container = upload_button.closest('div.fileinput-button');

      var success = function(data) {
        helpers.success('Upload complete!');
      };
      var failure = function() {
        helpers.error('Upload failed!');
        // TODO: Unset filename, hide file name div & re-show upload button
      };

      upload_button.bind('change', function(e) {
        var filename = e.target.files[0].name;
        var filename_elem = $($(this).data('filename-span-selector'));
        var filename_container = filename_elem.closest('div.filename-container');
        var spinner_id = $(this).data('spinner-id');
        var save_url = $(this).data('save-url');
        container.hide();

        new S3Upload({
          file_dom_selector: upload_button_id,
          s3_sign_put_url: '/sign_s3/',

          onProgress: function(percent, message) {
            $('#' + spinner_id).show();
          },
          onFinishS3Put: function(s3_url) {
            console.log('s3 success: ' + s3_url);

            var split_url = s3_url.split('/');
            var hosting_id = split_url[split_url.length - 1];
            var data = {
              filename: filename,
              hosting_id: hosting_id,
              id: prod_id
            };
            $('#' + spinner_id).hide();
            filename_elem.html(filename);
            filename_container.show();
            helpers.ajax_save(save_url, data, spinner_id, success, failure);
          },
          onError: function(status) {
            helpers.error('Upload failed!');
            $('#' + spinner_id).hide();
            container.show();
          }
        });
      });
    },
    upload: function(upload_container_id, upload_button_id, hidden_input_id,
                          filename_id, filename_container_id, data, spinner_id,
                          progress_id, progress_details_id, success_callback,
                          fail_callback) {
      var container = $('#' + upload_container_id);
      var upload_button = $('#' + upload_button_id);
      var hidden_input = $('#' + hidden_input_id);
      var filename = $('#' + filename_id);
      var filename_container = $('#' + filename_container_id);
      var post_url = upload_button.data('post-url');
      var progress_bar = $('#' + progress_id);
      var progress_details = $('#' + progress_details_id);

      upload_button.fileupload({
        url: post_url,
        maxChunkSize: 1000000,
        formData: data,
        dataType: 'json'
      }).prop('disabled', !$.support.fileInput).parent()
          .addClass($.support.fileInput ? undefined : 'disabled');

      upload_button.bind('fileuploadfail', function(e, data) {
        var server_msg = data.jqXHR.responseJSON.message;
        $('#' + spinner_id).hide();
        hidden_input.val('');
        container.show();
        progress_bar.removeClass('progress-bar-success');
        progress_bar.addClass('progress-bar-danger');
        helpers.warning(server_msg);
        fail_callback(server_msg);
      }).bind('fileuploadprogress', function(e, data) {
        var hr_loaded = helpers.hr_bytes(data.loaded);
        var hr_total = helpers.hr_bytes(data.total);
        var hr_speed = helpers.hr_bytes(data.bitrate);
        progress_details.find('span#current-p').html(hr_loaded[0]);
        progress_details.find('span#total-p').html(hr_total[0] + " " + hr_total[1]);
        progress_details.find('span#upload-speed').html(hr_speed[0] + " " + hr_speed[1]);
        var progress = parseInt(data.loaded / data.total * 100, 10);
        progress_bar.css('width', progress + '%');
        progress_bar.html(progress + '%');
      }).bind('fileuploaddone', function(e, data) {
        var file_name = data.result.filename;
        $('#' + spinner_id).hide();
        filename.html(data.result.filename);
        filename_container.show();
        progress_bar.parents('div#upload-progress').removeClass('active').hide();
        helpers.success('File uploaded successfully');
        success_callback(filename);
      }).bind('fileuploadchunkdone', function(e, data) {
        data.formData.uuid = data.result.uuid;
      }).bind('fileuploadchange', function(e, data) {
        var filename = data.files[0].name;
        hidden_input.val(filename);
        container.hide();
        progress_bar.parents('div#upload-progress').show();
        $('#' + spinner_id).show();
      });
    },
    hr_bytes: function(bytes) {
      var bytes = parseInt(bytes, 10);
      var types = ['bytes', 'KB', 'MB', 'GB', 'TB'];
      for (var x in types) {
          if (bytes < 1024) {
            return [Math.round((bytes * 100) / 100), types[x]];
          } else {
            bytes /= 1024
          }
      }
    },
    base58_decode: function (string) {

      var ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
      var ALPHABET_MAP = {};
      for(var i = 0; i < ALPHABET.length; ++i) {
        ALPHABET_MAP[ALPHABET.charAt(i)] = i;
      }
      var BASE = 58;

      if (string.length === 0) return [];

      var i, j, bytes = [0];
      for (i = 0; i < string.length; ++i) {
        var c = string[i];
        if (!(c in ALPHABET_MAP)) throw new Error('Non-base58 character');

        for (j = 0; j < bytes.length; ++j) bytes[j] *= BASE
        bytes[0] += ALPHABET_MAP[c];

        var carry = 0;
        for (j = 0; j < bytes.length; ++j) {
          bytes[j] += carry;

          carry = bytes[j] >> 8;
          bytes[j] &= 0xff;
        }

        while (carry) {
          bytes.push(carry & 0xff);

          carry >>= 8;
        }
      }

      // deal with leading zeros
      for (i = 0; string[i] === '1' && i < string.length - 1; ++i) bytes.push(0)

      return bytes.reverse()
    }

  };

  $("#comm_name").bind("blur", function() {
    var _this = $(this);
    var _fcf = $("#comm_name_fcf");
    var url = "/api/check_community/" + _this.val();
    _this.parent("div").find("div.help-block").hide().find("ul").find("li").remove();

    if (_this.val() === '') { return }
    if (_this.val().length < 4 || _this.val().length > 32) {
      _this.parent("div").find("div.help-block").show().find("ul").append("<li>Name must be 4-32 characters long</li>");
      _this.parent("div").addClass('has-error');
      return
    }

    var success = function(data) {
      if (data.available) {
        _this.parent("div").find("div.help-block").hide().find("ul").find("li").remove();
        _this.parent("div").removeClass('has-error');
        _this.parent("div").addClass('has-success');
        _fcf.removeClass("fa-spinner fa-spin fa-ban");
        _fcf.addClass("fa-check");
      } else {
        _this.parent("div").find("div.help-block").show().find("ul").append("<li>That name is not available</li>");
        _this.parent("div").removeClass('has-success');
        _this.parent("div").addClass('has-error');
        _fcf.removeClass("fa-spinner fa-spin fa-check");
        _fcf.addClass("fa-ban");
      }
    };
    var fail = function(data) {
      _this.parent("div").find("div.help-block").show().find("ul").append("<li>Failed to connect to server!</li>");
    };

    _fcf.show();
    helpers.ajax_check(url, success, fail);
  });


  // init collapsers
  $('.collapsible').collapse();
  $('.comment').collapse();

  var toggle = function(html) {
    if (html == '[-]') { return "[+]" } else { return "[-]" }
  };

  $(".collapser").bind("click", function(e) {
    e.stopPropagation();
    $(this).closest(".comment").children(".comment").collapse('toggle');
    $(this).closest(".media").find(".collapsible").collapse('toggle');
    $(this).html(toggle($(this).html()))
  });

});
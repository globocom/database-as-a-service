Base = window.Base || {};

Base.init = function(options) {
  Base.DbaasNotification.init(options);
}

Base.DbaasNotification = {};

(function (window, document, $) {
    'use strict';

    var url, $container, self;

    function init(config) {
      self = this;
      self.url = config.url;
      self.taskUrl = config.taskUrl;
      self.$container = $("#dropdown-menu-notification");

      setInterval(
        self.do_ajax,
        10000,
        {method: "GET",
          url: self.url},
        self.update_notification
      );

      bindEvents();
    }

    function bindEvents() {
      self.$container.on("click", function () {
        self.resetNotification(this);
      });
      $("#dropdown-menu-notification li.new .notify-info").on("click", function(event) {
        markAsRead($(this).closest('li'));
      });
    }

    function markAsRead($el) {

      var tasks = [],
        liData = $el.data();
      tasks.push({id: liData.taskId, status: liData.taskStatus, fields: [{'read': 1}]});

      $.ajax({
        url : self.url,
        type: 'POST',
        async: false,
        cache: false,
        data: JSON.stringify({ids: tasks})
      });
    }

    // TODO: remove that method and use $.ajax
    function do_ajax(conf, callback) {

      var xmlhttp = new XMLHttpRequest();

      xmlhttp.onreadystatechange = function() {
          if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
             if (xmlhttp.status == 200) {
                 if (callback) callback(xmlhttp.responseText);

             }
             else if (xmlhttp.status == 400) {
                console.log('There was an error 400');
             }
             else {
                 console.log('something else other than 200 was returned');
             }
          }
      }

      xmlhttp.open(conf.method, conf.url, true);
      xmlhttp.send(conf.payload);
    }

    function replaceCssClass($el, actual_class, new_class) {
      $el.addClass(new_class);
      $el.removeClass(actual_class);
    }

    function resetNotificationCnt() {
      var $notificationContainer = $("#dropdown-menu-notification");
      var $notificationCnt = $notificationContainer.find(".notification-cnt");
      replaceCssClass($notificationCnt, "badge-warning", "badge-default");
      $notificationCnt.text("0");
    }

    function resetNotification(el) {
      el = el || $("#dropdown-menu-notification");
      var lis = $(el).find("ul li[data-task-id]").toArray(),
        ids = [],
        li,
        liData;

      for (var pos in lis) {
        li = lis[pos];
        liData = $(li).data();
        if (liData.isNew) ids.push({id: liData.taskId, status: liData.taskStatus});
      }

      if (ids.length) {
        self.do_ajax(
          {
            method: "POST",
            url: self.url,
            payload: JSON.stringify({ids: ids})
          },
          self.resetNotificationCnt
        );
      }
    }

    function mouseLeaveNotification() {
      $("#dropdown-menu-notification .dropdown-toggle").eq(0).removeClass('active');
    }

    function update_notification(data) {
      var json = JSON.parse(data);

      var view = {
        resp: json,
        isNew: function() {
          return parseInt(this.is_new) ? 1 : undefined;
        },
        notificationQuantity: function() {
          var obj,
              cont = 0;
          for (var pos in this.resp) {
              obj = this.resp[pos];
              if (parseInt(obj.is_new)) cont++;
          }

          return cont;
        },
        databaseName: function() {
          if (this.database_name) {
            return this.database_name;
          }
          var regex = /database( name)?: ([\w-_\ ]+),?/i;
          var parsedArguments = this.arguments.match(regex);
              if (parsedArguments) {
                  return parsedArguments[2];
              }
          return "not found";
        },
        parseTaskName: function() {
          var splitedTaskName = this.task_name.split(".");
          return splitedTaskName[splitedTaskName.length - 1];
        },
        statusCssClass: function() {
          // Pegar isso da view ou de outro lugar
          var taskStatus = this.task_status;
          if (taskStatus === "RUNNING") return "warning";
          if (taskStatus === "WAITING") return "inverse";
          if (taskStatus === "ERROR") return "important";
          if (taskStatus) return taskStatus.toLowerCase();
        },
        notReadClass: function() {
          if (!parseInt(this.read)) return 'new';
          return ''
        },
        taskUrl: function() {
          return self.taskUrl
        }
      }

      var template = `
        {{ #resp }}
          <li class="{{ notReadClass }}" data-task-id="{{ task_id }}" data-task-status="{{ task_status }}" data-is-new="{{ is_new }}">
              <a href="{{ taskUrl }}?id={{ task_id }}" class="notify-info">
                <span class="notify-label"><span class="label label-{{ statusCssClass }}">{{ task_status }}</span></span>
                <span class="notify-body">
                  <div class="notify-task"><span class="notify-description">task name:</span> {{ parseTaskName }}</div>
                  <div class="notify-database"><b>database:</b> {{ databaseName }}</div>
                </span>
              </a>
            </li>
          {{ /resp }}
          {{ ^resp }}
            <li class="no-notification">No tasks found.</li>
          {{ /resp }}
      `;
      var html = Mustache.render(template, view);

      $("#dropdown-menu-notification .dropdown-menu").html(html);
      var notificationQuantity = view.notificationQuantity(),
        $notificationCount = $("#dropdown-menu-notification .notification-cnt");
      if ($("#dropdown-menu-notification.open").length === 0) {
        if (notificationQuantity != parseInt($notificationCount.text())) {
          $notificationCount.text(view.notificationQuantity());
          replaceCssClass($notificationCount, "badge-default", "badge-warning");
        }
      }
      else {
        resetNotification();
      }
  }

  $.extend(
    Base.DbaasNotification,
    {
      init: init,
      do_ajax: do_ajax,
      update_notification: update_notification,
      resetNotification: resetNotification,
      resetNotificationCnt: resetNotificationCnt
    }
  );

})(window, document, django.jQuery);

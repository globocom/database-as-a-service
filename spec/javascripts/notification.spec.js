// TODO: Remove this django.jQuery from html for i use jquery the right way
django = {}
$ = require ('../../dbaas/admin/static/admin/js/jquery-3.2.1.min.js');
django.jQuery = $
Mustache = require ('../../dbaas/admin/static/admin/js/mustache2.js');
require('../../dbaas/admin/static/admin/js/notification.js');


describe("DbaasNotification test case", function() {

  function updateNotification(tasks) {
    Base.DbaasNotification.update_notification(JSON.stringify(tasks));
  }

  describe("Initialization", function() {

    beforeEach(function() {
      jest.useFakeTimers();
      Base.init({'url': '/fake/url/'});
    });

    it("setInterval", function() {

      expect(setInterval).toBeCalled();
      expect(setInterval).toBeCalledWith(
        Base.DbaasNotification.do_ajax,
        10000,
        {method: 'GET', url: '/fake/url/'},
        Base.DbaasNotification.update_notification
      );

    });
  });

  describe("bindEvents", function() {

    afterAll(function() {
      Base.DbaasNotification.resetNotification.mockRestore();
    });

    beforeEach(function() {

      document.body.innerHTML =
        '<div class="dropdown pull-right welcome-message" id="dropdown-menu-notification">' +
        '  <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel" >' +
        '  </ul>' +
        '</div>';
      jest.spyOn(Base.DbaasNotification, 'resetNotification').mockImplementation(function() { return true });
      Base.init({'url': '/fake/url/'});
    });

    afterEach(function() {
      Base.DbaasNotification.resetNotification.mockReset();
    });

    it("Call method when click on menu", function() {
      $("#dropdown-menu-notification").click();

      expect(Base.DbaasNotification.resetNotification).toBeCalled();
    });
  });

  describe("Notification count", function() {
    var fake_task_1, fake_task_2;

    beforeEach(function() {

      document.body.innerHTML =
        '<div class="dropdown pull-right welcome-message" id="dropdown-menu-notification">' +
        '  <a class="dropdown-toggle uni" id="dLabel" role="button" data-toggle="dropdown" data-target="#" href="#">' +
        '    <i class="icon-bell icon-white"></i>' +
        '    Notifications <span class="badge badge-default notification-cnt">0</span>' +
        '  </a>' +
        '  <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel" >' +
        '  </ul>' +
        '</div>';

      Base.init({'url': '/fake/url/'});

      fake_task_1 = {
        task_id: 1,
        updated_at: 1501530487,
        is_new: 1,
        arguments: 'Database: fake_redis_1, New Disk Offering: Micro',
        task_name: 'database_disk_resize',
        task_status: 'SUCCESS',
        user: 'admin'
      }
      fake_task_2 = {
        task_id: 2,
        updated_at: 1501530400,
        is_new: 1,
        arguments: 'Database: fake_redis_2, New Disk Offering: Micro',
        task_name: 'database_destroy',
        task_status: 'RUNNING',
        user: 'admin'
      }

    });

    it("Has badge-default when count 0", function() {

      updateNotification([]);
      var $notificationCnt = $(".badge-default.notification-cnt");

      expect($notificationCnt.length).toBe(1);
      expect($notificationCnt.text()).toBe("0")
    });

    it("Has badge-warning when count greater than 0", function() {


      updateNotification([fake_task_1]);
      var $notificationCnt = $(".badge-warning.notification-cnt");

      expect($notificationCnt.length).toBe(1);
    });

    it("Count 1 when has 1 item", function() {

      updateNotification([fake_task_1]);
      var $notificationCnt = $(".notification-cnt").text();

      expect($notificationCnt).toBe("1")
    });

    it("Count 1 when has 1 item but only one is new", function() {

      fake_task_2.is_new = 0;
      updateNotification([fake_task_1, fake_task_2]);
      var $notificationCnt = $(".notification-cnt").text();

      expect($notificationCnt).toBe("1")
    });

    it("Count 2 when has 2 items", function() {

      updateNotification([fake_task_1, fake_task_2]);
      var $notificationCnt = $(".notification-cnt").text();

      expect($notificationCnt).toBe("2")
    });

    it("Task name is right", function() {

      updateNotification([fake_task_1]);
      var taskName = $(".notify-task").text();

      expect(taskName).toBe("task name: database_disk_resize")
    });

    it("Database name is right", function() {

      updateNotification([fake_task_1]);
      var databaseName = $(".notify-database").text();

      expect(databaseName).toBe("database: fake_redis_1")
    });

    it("Task status", function() {

      updateNotification([fake_task_1, fake_task_2]);
      var $labelSuccess = $(".label-success");
      var $labelRunning = $(".label-warning");

      expect($labelSuccess.length).toBe(1);
      expect($labelRunning.length).toBe(1);
      expect($labelSuccess.text()).toBe("SUCCESS");
      expect($labelRunning.text()).toBe("RUNNING");
    });
  });

  describe("resetNotification", function() {

    var fake_task_1, fake_task_2;

    afterAll(function() {
      Base.DbaasNotification.do_ajax.mockRestore();
    });

    beforeEach(function() {

      document.body.innerHTML =
        '<div class="dropdown pull-right welcome-message" id="dropdown-menu-notification">' +
        '  <a class="dropdown-toggle uni" id="dLabel" role="button" data-toggle="dropdown" data-target="#" href="#">' +
        '    <i class="icon-bell icon-white"></i>' +
        '    Notifications <span class="badge badge-default notification-cnt">0</span>' +
        '  </a>' +
        '  <ul class="dropdown-menu" role="menu" aria-labelledby="dLabel" >' +
        '  </ul>' +
        '</div>';

      Base.init({'url': '/fake/url/'});

      fake_task_1 = {
        task_id: 1,
        updated_at: 1501530487,
        is_new: 1,
        arguments: 'Database: fake_redis_1, New Disk Offering: Micro',
        task_name: 'database_disk_resize',
        task_status: 'SUCCESS',
        user: 'admin'
      }
      fake_task_2 = {
        task_id: 2,
        updated_at: 1501530400,
        is_new: 1,
        arguments: 'Database: fake_redis_2, New Disk Offering: Micro',
        task_name: 'database_destroy',
        task_status: 'RUNNING',
        user: 'admin'
      }

      jest.spyOn(Base.DbaasNotification, 'do_ajax').mockImplementation(function() {});
    });

    afterEach(function() {
      Base.DbaasNotification.do_ajax.mockReset();
    });


    it("Call ajax when all items is new", function() {

      updateNotification([fake_task_1, fake_task_2]);
      Base.DbaasNotification.resetNotification();

      expect(Base.DbaasNotification.do_ajax).toBeCalled()
      expect(Base.DbaasNotification.do_ajax).toBeCalledWith(
        {
          method: 'POST',
          url: '/fake/url/',
          payload: JSON.stringify({ids: [{id: 1, status: "SUCCESS"}, {id: 2, status: "RUNNING"}]})
        },
        Base.DbaasNotification.resetNotificationCnt
      )
    });

    it("Call ajax only for new items", function() {

      fake_task_1.is_new = 0;
      updateNotification([fake_task_1, fake_task_2]);
      Base.DbaasNotification.resetNotification();

      expect(Base.DbaasNotification.do_ajax).toBeCalled()
      expect(Base.DbaasNotification.do_ajax).toBeCalledWith(
        {
          method: 'POST',
          url: '/fake/url/',
          payload: JSON.stringify({ids: [{id: 2, status: "RUNNING"}]})
        },
        Base.DbaasNotification.resetNotificationCnt
      )
    });

    it("Ajax not called when all items are old", function() {

      fake_task_1.is_new = 0;
      fake_task_2.is_new = 0;
      updateNotification([fake_task_1, fake_task_2]);
      Base.DbaasNotification.resetNotification();

      expect(Base.DbaasNotification.do_ajax).not.toBeCalled()
    });
  });
});

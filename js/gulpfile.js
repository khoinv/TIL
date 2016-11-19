// example gulp file

var gulp = require('gulp'),
    browserSync = require('browser-sync'),
    reload = browserSync.reload;

// define task name
gulp.task('default', [], function () {
    console.log("Command:\n   serve - run live reload server");
});


// define serve task
gulp.task('serve', [], function () {
    browserSync({
        notify: false,
        server: {
            baseDir: '.'
        }
    });

    gulp.watch(['*.html'], reload);
    gulp.watch(['js/*.js'], reload);
});

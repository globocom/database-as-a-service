var is_dark = localStorage.getItem('darkmode');

var setDarkMode = function(){
    console.log('add dark')
}

var removeDarkMode = function(){
    console.log('remove dark')
}


if (!is_dark)
    is_dark = false;

if (is_dark){
    setDarkMode();
}

localStorage.setItem('darkmode', is_dark);
var Validator = {};
  (function(){

    var validateAll = function(event)
    {
      var inputs = document.getElementsByClassName("new_custom_value_input");
      var valuesAreValid = true;
      for (var i = 0; i < inputs.length; i++){
        if( !validateSingleInput( $(inputs[i]) ) )
          valuesAreValid = false;
      }
      if(!valuesAreValid){
        event.preventDefault();
        event.stopPropagation();
      }
    }

    var validateSingleInput = function(inputElement){
      var currentInput = inputElement;
      var errorMessage = currentInput.parents("tr").find(".error_message");
      errorMessage.hide();
      currentInput.css('border', '1px solid #ccc');

      var currentType = currentInput.parents("tr").find(".type_meta").val().trim();
      var currentAllowedValues = currentInput.parents("tr").find(".allowed_values_meta").val().trim();
      if(!validateNewValue(currentInput.val(), currentType, currentAllowedValues)){
        currentInput.css('border', '1px solid #ff0000');
        errorMessage.show();
        return false;
      }

      return true;
    }

    var validateNewValue = function(value, acceptableType, allowedValues){
      if(value==''){
        return true;
      }
      if (acceptableType=="string") {
        return validateString(value, allowedValues)
      }
      if (acceptableType=="integer") {
        var numericVal = +value;
        if(numericVal!=parseInt(numericVal,10))
          return false;

        return validateNumber(value, allowedValues)
      }
      if (acceptableType=="float") {
        return validateNumber(value, allowedValues)
      }
      if (acceptableType=="boolean") {
        return true;
      }
      return false;
    }

  var validateNumber = function(value, allowedValues){
    var numericVal = +value;

    if(isNaN(numericVal))
      return false;

    if(allowedValues == "")
      return true;

    var allowedSet = allowedValues.split(/\s*[\s,]\s*/)
    for (var i in allowedSet) {
      if( isNaN(+allowedSet[i]) ){
        if(testNumberRange(value, allowedSet[i]))
          return true;
      }
      else if (value == +allowedSet[i]) {
        return true;
      }
    }

    return false;
  }

  var testNumberRange = function(value, range){
    var nums = range.split(/\s*[\s:]\s*/)
    var lowerLimit = +nums[0]
    if(nums[1] != ""){
      var upperLimit = +nums[1]
      if(value >= lowerLimit && value <= upperLimit){
        return true;
      }
    }
    else {
      if(value>=lowerLimit){
        return true;
      }
    }
    return false;
  }

  var validateString = function(value, allowedValues){
    if(allowedValues=="")
      return true;

    var allowedSet = allowedValues.split(/\s*[\s,]\s*/)
    for (var i in allowedSet) {
      if (value == allowedSet[i]) {
        return true;
      }
    }
    return false;
  }

    $.extend(
      Validator,
      {validateAll: validateAll},
      {validateSingleInput: validateSingleInput})

  })();

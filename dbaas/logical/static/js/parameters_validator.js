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
        
        try {
          var bigVal = new BigNumber(value)
        } catch (err) {
          return false;
        }

        if(value.indexOf('.') !== -1)
          return false;

        return validateNumber(bigVal, allowedValues)
      }
      if (acceptableType=="float") {
        if(value.indexOf('.') == -1)
          return false;

        try {
          var bigVal = new BigNumber(value)
        } catch (err) {
          return false;
        }
        return validateNumber(bigVal, allowedValues)
      }
      if (acceptableType=="boolean") {
        return true;
      }
      return false;
    }

  var validateNumber = function(value, allowedValues){
    // var numericVal = +value;

    if(value.isNaN())
      return false;

    if(allowedValues == "")
      return true;

    var allowedSet = allowedValues.split(/\s*[,]\s*/)
    for (var i in allowedSet) {
      try{
        var constraintVal = new BigNumber(allowedSet[i])

        if ( value.equals(constraintVal) ) {
          return true;
        }

      } catch (err) {
        if( testNumberRange(value, allowedSet[i]) ){
          return true;
        }
      }
    }

    return false;
  }

  var testNumberRange = function(value, range){
    var nums = range.split(/\s*[:]\s*/)
    var lowerLimit = new BigNumber( nums[0] )
    if(nums[1] != ""){
      var upperLimit = new BigNumber( nums[1] )
      if( value.gte(lowerLimit) && value.lte(upperLimit) ){
        return true;
      }
    }
    else {
      if( value.gte(lowerLimit) ){
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



Version			:	 	1.0

Date 				:		March 20, 2024

Reviewed By			:		Rohith R

Approved By			:		InappTMO

Author(s) of the document	:		Darshna Venugopal, Anupam B

**Revision History**

| Revision No. | Description of Version and Source Of Change | Date Of Change | Primary Author(s) |
| :---: | ----- | ----- | ----- |
|  1.0 | The first version of the Detailed  Coding Standards and Best Practices for Python Development | March 20, 2024  | Darshna Venugopal,  Anupam B |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

**Version Approvals**

| Version | InApp Approval(TMO Convenor) | Approved / Rejected |
| :---- | ----- | :---: |
| 1.0 | **InappTMO** | **Approved** |
|  |  |  |

**Availability**

The original document shall be available with TMO.

 

**TABLE OF CONTENTS** 

[Introduction](#introduction)

[Naming Conventions](#naming-conventions)

[1\. General](#general)

[2\. Packages](#packages)

[3\. Modules](#modules)

[4\. Classes](#classes)

[5\. Global (module-level) Variables](#global-\(module-level\)-variables)

[6\. Instance Variables](#instance-variables)

[7\. Methods](#methods)

[8\. Method Arguments](#method-arguments)

[9\. Functions](#functions)

[10\. Constants](#constants)

[Code Structure and Layout](#code-structure-and-layout)

[a. Indentation](#indentation)

[b. Line Length](#line-length)

[c. Import Statements](#import-statements)

[d. Whitespace](#whitespace)

[e. Comments](#comments)

[Python Features and Best Practices](#python-features-and-best-practices)

[A. Python 2 vs. Python 3](#python-2-vs.-python-3)

[B. Virtual Environment](#virtual-environments)

[C. Exception](#exception-handling) Handling

[D. List](#list-comprehensions) Comprehensions

[E. Lambda Functions](#lambda-functions)

[F. Generators](#generators)

[G. Decorators](#decorators)

[H. Global and Local Variables](#global-and-local-variables)

[Documentation and Docstrings](#documentation-and-docstrings)

[1\. Docstrings](#docstrings)

[2\. Inline Comments](#inline-comments)

[3\. Tools for Generating Documentation](#tools-for-generating-documentation)

[Testing](#testing)

[Guidelines for Writing Unit Tests](#guidelines-for-writing-unit-tests)

[Packaging and Project Organization](#packaging-and-project-organization)

[Directory Structure](#directory-structure)

[Packaging](#packaging)

[Version Control](#version-control)

[Virtual Environments](#virtual-environments-1)

[Documentation](#documentation)

[Testing](#testing-1)

[Code Style and Linting](#code-style-and-linting)

[Dependency Management](#dependency-management)

[Isolation and Modularity](#isolation-and-modularity)

[Style Guide](#style-guide)

[Python Language Rules](#python-language-rules)

[Python Style Rules](#python-style-rules)

[Performance Considerations](#performance-considerations)

[1\. Techniques for optimizing Python code](#techniques-for-optimizing-python-code)

[Security Considerations](#security-considerations)

[1\. Input Validation and Sanitization:](#input-validation-and-sanitization:)

[2\. Avoiding Hardcoded Credentials:](#avoiding-hardcoded-credentials:)

[3\. Secure File Handling:](#secure-file-handling:)

[4\. SSL/TLS Usage:](#ssl/tls-usage:)

[5\. Dependency Scanning:](#dependency-scanning:)

[6\. Code Review for Security:](#code-review-for-security:)

[7\. Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF) Mitigation:](#cross-site-scripting-\(xss\)-and-cross-site-request-forgery-\(csrf\)-mitigation:)

[8\. Authentication and Authorization:](#authentication-and-authorization:)

[9\. Logging and Monitoring:](#logging-and-monitoring:)

[10\. Data Encryption:](#data-encryption:)

[Portabilit](#portability)y

[Version Control](#version-control-1)

	

# Introduction  {#introduction}

Coding guidelines are an indispensable component of modern software development. They provide a structured framework of rules and conventions for writing code in a consistent and readable manner. In the context of Python, a language renowned for its elegance and readability, adhering to these guidelines is paramount for producing high-quality, maintainable, and efficient software. 

This document explores the significance of coding guidelines and underscores the numerous advantages of their strict adherence. Guidelines are vital for achieving code excellence and seamless collaboration within development teams.

# Naming Conventions {#naming-conventions}

Consistency and readability are crucial when following naming conventions. Others may read the code, so choose names that are self-explanatory and document code effectively. When in doubt, adhere to the PEP 8 style guide for Python, which provides a comprehensive set of coding style recommendations for Python code. Consistent naming conventions make the code more accessible and maintainable, benefiting everyone on the team. 

1. ### **General** {#general}

     
* Adhere to naming practices that balance specificity and brevity. Avoid overly generic or excessively verbose names.

  * **Less Desirable**:

    * data\_structure

    * my\_list

    * info\_map

    * dictionary\_for\_the\_purpose\_of\_storing\_data\_representing\_word\_definitions

  * **Preferred**:

    * user\_profile

    * menu\_options

    * word\_definitions

* Furthermore, exercise discretion and refrain from using overly obscure or cryptic names like "O," "l," or "I."

* When employing CamelCase for names, ensure that all letters in an abbreviation are capitalized. For instance, use "HTTPServer" instead of "HttpServer."

2. ### **Packages** {#packages}

     
* Package names should be all lowercase  
* When multiple words are needed, an underscore should separate them  
* It is usually preferable to stick to 1-word names


3. ### **Modules** {#modules}

     
* Module names should be all lowercase  
* When multiple words are needed, an underscore should separate them  
* It is usually preferable to stick to 1-word names  
* Module names should be short, descriptive, and related to the module's content.  
* Avoid naming modules with common Python module names (e.g., math, datetime).

4. ### **Classes** {#classes}

     
* Class names should follow the UpperCaseCamelCase convention  
* Class names should be nouns or noun phrases describing the class's purpose.  
* Python’s built-in classes, however, are typically lowercase words  
* Exception classes should end in “Error”

5. ### **Global (module-level) Variables** {#global-(module-level)-variables}

     
* Global variables should be all lowercase  
* Words in a global variable name should be separated by an underscore


6. ### **Instance Variables** {#instance-variables}

     
* Instance variable names should be all lowercase  
* Words in an instance variable name should be separated by an underscore  
* Non-public instance variables should begin with a single underscore  
* If an instance name needs to be mangled, two underscores may begin its name


7. ### **Methods** {#methods}

     
* Method names should be all lowercase  
* Words in a method name should be separated by an underscore  
* Non-public method should begin with a single underscore  
* If a method name needs to be mangled, two underscores may begin its name


8. ### **Method Arguments** {#method-arguments}

     
* Instance methods should have their first argument named ‘self’.  
* Class methods should have their first argument named ‘cls’


9. ### **Functions** {#functions}

     
* Function names should be all lowercase  
* Words in a function name should be separated by an underscore  
* Use verbs to describe the action the function performs (e.g., calculate\_average()).  
* Make function names clear and concise.


10. ### **Constants** {#constants}

      
* Constants should represent values that are not meant to change during the program's execution.  
* Constant names must be fully capitalized  
* Words in a constant name should be separated by an underscore (e.g., MAX\_VALUE).

# Code Structure and Layout {#code-structure-and-layout}

Maintaining a well-organized code structure is essential for readability and maintainability. Use consistent and meaningful naming conventions for your functions, classes, and variables. Group related functions and classes together, and make use of whitespace to separate logical sections within your code.

1. ### **Indentation** {#indentation}

   Python uses indentation to define code blocks, and adhering to a consistent indentation style is crucial for code clarity. We recommend using 4 spaces per level of indentation as it's the most widely accepted convention in the Python community.

2. ### **Line Length** {#line-length}

   To ensure your code remains readable, keep your lines within a reasonable length. A common guideline is to limit lines to 79-80 characters. For longer expressions or function calls, break them into multiple lines, maintaining a clear and consistent structure.

3. ### **Import Statements** {#import-statements}

   Organize import statements at the top of your code and follow the standard library imports, third-party library imports, and your own module imports in separate blocks. Use absolute or explicit relative import paths for clarity.

4. ### **Whitespace** {#whitespace}

   Proper use of whitespace is essential for code aesthetics. Use blank lines to separate functions, classes, and logical sections of your code. Within functions, add whitespace to separate code blocks and improve readability.

5. ### **Comments** {#comments}

   Comments play a vital role in code documentation. Write clear, concise comments to explain the purpose of functions, classes, and complex code segments. Maintain up-to-date comments to ensure that the code remains understandable, even as it evolves.

   

# Python Features and Best Practices {#python-features-and-best-practices}

Python is a versatile and powerful programming language with a rich ecosystem of libraries and frameworks. To make the most of Python's capabilities, it's important to follow best practices and understand key features of the language. In this section, we'll explore essential aspects of Python programming and guidelines for writing clean and maintainable code.

1. ### **Python 2 vs. Python 3** {#python-2-vs.-python-3}

   Python 2 and Python 3 are two major versions of the language, and it's crucial to understand the key differences between them. 

   Python 2 has reached its end of life and is no longer supported, so it is strongly recommended to use Python 3 for all new projects. When transitioning from Python 2 to Python 3, be aware of changes in syntax, library names, and Unicode handling.

   **Best Practice**: Always use Python 3 for new development and consider migrating existing Python 2 codebases to Python 3 to ensure compatibility and access to the latest features.

2. ### **Virtual Environments** {#virtual-environments}

   Virtual environments are essential for isolating Python projects, and their dependencies, and avoiding conflicts between packages. Python's built-in ***venv*** module or third-party tools like ***virtualenv*** are used to create isolated environments for projects.  
     
   **Best Practice**: Create a virtual environment for each project to manage its dependencies separately, ensuring a clean and isolated development environment.

3. ### **Exception Handling** {#exception-handling}

   Exception handling is a fundamental concept in Python. It allows you to gracefully handle errors and exceptions that may occur during program execution. Use try, except, and finally blocks to handle exceptions effectively.  
     
   **Best Practice**:   
   Catch specific exceptions, provide informative error messages, and avoid using broad exception handlers whenever possible.

1. #### **Use Specific Exceptions**

   Catching specific exceptions is akin to using specialized tools for different tasks. Instead of relying on a generic catch-all statement, it’s essential to catch specific exception types. This practice allows to differentiate between various errors and deliver accurate error messages, making issue identification and resolution more efficient.

   

2. #### Implement Error Logging

   Utilizing the logging module, we can capture exceptions and vital information like timestamps, error details, and stack traces. This empowers the analysis of errors comprehensively and enhances the reliability of the application.

   

3. #### Define Custom Exception Classes

   Custom exception classes in Python allow developers to create custom exception classes that cater to the application’s unique needs. By doing so, we can categorize and encapsulate different errors, leading to better code readability, improved error handling, and modular project development.

   

4. #### Handle Exceptions Gracefully

   To prevent application crashes and user confusion, employ try-except blocks to catch exceptions. This allows developers to provide suitable error messages or alternative actions. Graceful error handling enhances user experience, maintains application flow, and safeguards against security vulnerabilities.

5. #### Use Finally for Cleanup Tasks

   The finally block in exception handling ensures that certain code will execute regardless of whether an exception occurred or not. This is ideal for performing cleanup tasks, such as closing files or releasing resources, and maintaining the application’s integrity.

   

4. ### **List Comprehensions** {#list-comprehensions}

   List comprehensions provide a concise and readable way to create lists in Python. They are a Pythonic approach for generating lists based on existing ones or other iterables.  
     
   It provides developers with a simple way to create a list based on some sequence or another list that we can loop over. In Python terminology, anything that loop over is called iterable. At its most basic level, list comprehension is a syntactic construct for creating lists from existing lists. In the core of list comprehension, it is the loop (‘for’ loop). Any list comprehension can be represented as a for loop, but when we represent it with equivalent list comprehension in a single line, it looks genuinely unique.  
     
   **Best Practice**: Use list comprehensions when appropriate to make the code more concise and expressive.  
   

5. ### **Lambda Functions** {#lambda-functions}

   Lambda functions, also known as anonymous functions, are small, one-line functions defined using the lambda keyword. They are often used for simple operations, such as sorting and filtering data.  
     
   **Best Practice**: Use lambda functions for short, simple operations, but be mindful of readability and avoid complex logic within lambda functions.  
   

6. ### **Generators** {#generators}

   Generators are a memory-efficient way to produce a sequence of values in Python. They use the yield keyword to generate values on the fly rather than creating and storing them all in memory.  
     
   **Best Practice**: Use generators for large datasets or when you need to create sequences of data without consuming excessive memory.

7. ### **Decorators** {#decorators}

   Decorators are a powerful feature in Python that allows to modify or enhance the behavior of functions or methods. They are widely used for tasks like logging, authentication, and profiling.  
     
   **Best Practice**: Apply decorators to functions when you want to add behavior or functionality without modifying their source code directly.

8. ### **Global and Local Variables** {#global-and-local-variables}

   Understanding variable scopes in Python is crucial. Variables can have global or local scope, and it's essential to be aware of the scope of variables to avoid unexpected behavior in your code.  
     
   **Best Practice**: Minimize the use of global variables and favor local variables whenever possible. Use descriptive variable names to enhance code readability.  
   

# Documentation and Docstrings {#documentation-and-docstrings}

Documentation is a crucial aspect of writing maintainable and understandable Python code. It provides insights into the purpose, functionality, and usage of your code. Properly documented code not only helps you understand your own work but also assists other developers who may collaborate with you or maintain your code in the future. One of the primary tools for documenting Python code is docstrings.

1. ### **Docstrings** {#docstrings}

   A docstring is a multi-line string that is the first statement in a module, function, class, or method. It serves as a form of inline documentation that provides information about the object it precedes. 

   Follow these best practices when writing docstrings:

   #### 1.1. Use Triple Quotes

   Enclose the docstring in triple quotes (single or double) to make it a multi-line string. This allows for more detailed and readable documentation.

   #### 

   #### def my\_function():

   ####     """

   ####     This is a sample docstring for my\_function.

   #### 

   ####     More detailed explanations and usage instructions can be provided here.

   ####     """

   ####     pass

#### 1.2. Be Descriptive

Write clear, concise, and descriptive docstrings. Explain what the function, class, or method does, its parameters, return values, and any exceptions it may raise.

#### 1.3. Use Appropriate Sections

Divide your docstring into sections to make it more structured and easier to navigate. Common sections include:

* **Parameters**: List and describe the function's parameters.  
* **Returns**: Explain what the function returns, including its type.  
* **Raises**: Document any exceptions that the function may raise.  
* **Examples**: Provide usage examples to demonstrate how to use the function.  
* **Notes**: Include any additional information that can help developers understand the code better.


  ***def divide(a, b):***

      **"""**

      **Divides two numbers.**


      **Parameters:**

      **a (int): The numerator.**

      **b (int): The denominator.**


      **Returns:**

      **float: The result of the division.**


      **Raises:**

      **ValueError: If the denominator is 0\.**


      **Examples:**

      **\>\>\> divide(6, 2\)**

      **3.0**

      **\>\>\> divide(5, 0\)**

      **Traceback (most recent call last):**

          **...**

      **ValueError: Division by zero**

      **"""**

      **if b \== 0:**

          **raise ValueError("Division by zero is not allowed.")**

      **return a / b**


  

#### 1.4. Keep Docstrings Updated

Maintain docstrings as your code evolves. Outdated or incorrect documentation can be more confusing than having no documentation at all.

2. ### **Inline Comments** {#inline-comments}

   While docstrings are used for high-level documentation, inline comments are used to provide clarifications within the code. 

   Use inline comments sparingly and follow these guidelines:

* Comment on complex or non-obvious sections of code to explain their purpose.  
* Be concise and clear in comments.  
* Avoid redundant or trivial comments. The code should be self-explanatory.


3. ### **Tools for Generating Documentation** {#tools-for-generating-documentation}

     
   Consider using tools like Sphinx, Doxygen, or auto-generating documentation from your docstrings using tools like **pydoc** or **Sphinx autodoc** for more extensive and organized documentation.

   Docstrings can enhance the clarity and maintainability of the Python code, making it easier for anyone to work with the codebase.

# Testing {#testing}

Testing is a critical aspect of software development in Python (and in any other programming language). It helps ensure that the code works as expected, detects bugs early in the development process, and provides a safety net for making changes and enhancements to the codebase. Proper testing also aids in maintaining code quality and reliability, making it an essential part of the development cycle.

### **Guidelines for Writing Unit Tests** {#guidelines-for-writing-unit-tests}

Writing effective unit tests is crucial to ensure the reliability of the code.   
Here are some guidelines to consider when creating unit tests in Python:

1. #### Isolation

   Unit tests should focus on testing a single unit of code, such as a function or method, in isolation. Dependencies on external resources, databases, or network services should be mocked or stubbed to keep tests independent.

2. #### Descriptive Test Names 

   Give your tests clear and descriptive names that convey their purpose. This makes it easier to understand what is being tested when reviewing results or failures.

3. #### Use Assertions

   Utilize assertions to validate the expected behavior of the code. Python's built-in assert statement is a useful tool for this purpose.

4. #### Test for Edge Cases 

   Ensure that the unit tests cover edge cases, boundary conditions, and any exceptional scenarios that the code might encounter.

5. #### Maintain Test Independence

   Each test should not depend on the system's state or other tests. Ensure that tests are self-contained and can be run individually.

6. #### Test Coverage

   Strive for good test coverage, aiming to test as many code paths as possible. Use coverage analysis tools to identify areas that need additional testing.

7. #### Continuous Integration

   Integrate the tests into a continuous integration (CI) system to automatically run them whenever changes are made to the codebase. This helps catch regressions early.

8. #### Documentation

   Include clear documentation for the tests, explaining their purpose and any specific conditions they rely on.

9. #### TDD (Test-Driven Development)

   Consider adopting a test-driven development approach where you write tests before writing the actual code. This helps you focus on the desired functionality and improves code design.

10. #### Regular Maintenance

    Unit tests should be maintained and updated as the code evolves. Outdated tests can become a liability rather than an asset.

# Packaging and Project Organization {#packaging-and-project-organization}

Properly structuring Python projects is crucial for code maintainability, scalability, and collaboration. A well-organized project enhances code readability, eases debugging, and simplifies the process of adding new features or modifying existing ones. 

### **Directory Structure** {#directory-structure}

Establishing a clear and consistent directory structure is the foundation of a well-organized project. A common practice is to follow the structure outlined in the Python Packaging Authority (PyPA) sample project layout. 

Here are some key elements of this structure:

### **![][image1]**

### **Packaging** {#packaging}

Package the project using setuptools and setup.py. This allows developers to distribute projects, install dependencies, and handle versioning. Make sure to include metadata such as the project name, version, author, and license in the setup.py file. Developers can generate a requirements.txt file using tools like pipenv, poetry, or conda.

### **Version Control** {#version-control}

Utilize version control systems like Git to track changes in the project. Hosting code on platforms like GitHub, GitLab, or Bitbucket makes it easier for team collaboration and provides a central location for code review and issue tracking.

### 

### **Virtual Environments** {#virtual-environments-1}

Always work within virtual environments to isolate project dependencies. Popular tools for creating virtual environments include **virtualenv**, **venv**, and package managers like **pipenv** and **conda**. This ensures that the project's dependencies do not interfere with the global Python environment.

### **Documentation** {#documentation}

Maintain comprehensive project documentation in the 'docs/' directory. Use tools like Sphinx to generate documentation from docstrings, and make sure to include information about installation, usage, and development guidelines.

### **Testing** {#testing-1}

Write unit tests for code and place them in the 'tests/' directory. Use testing frameworks like **unittest**, **pytest**, or **nose**. Continuous Integration (CI) tools, such as Travis CI, CircleCI, or GitHub Actions, can automate the testing process with each code commit.

### **Code Style and Linting** {#code-style-and-linting}

Enforce a consistent code style by adhering to the PEP 8 style guide. Developers can use tools like **flake8**, **pylint**, or **black** to automatically check and format code. This promotes readability and maintainability.

### **Dependency Management** {#dependency-management}

Keep a well-maintained 'requirements.txt' file that lists all project dependencies. Utilize a version pinning strategy to ensure consistent behavior across different environments.

### **Isolation and Modularity** {#isolation-and-modularity}

Organize the code into modules and packages, ensuring that each component has a specific purpose and responsibility. Avoid overly long modules and functions by following the Single Responsibility Principle (SRP).

# Style Guide {#style-guide}

Effective and consistent coding style is essential for maintaining clean and readable Python code. The below document provides comprehensive guidance on adhering to the Python Enhancement Proposal 8 (PEP 8), which is the de facto style guide for Python. 

### **Python Language Rules** {#python-language-rules}

1. #### Lint

   **pylint** is a tool for finding bugs and style problems in Python source code. Because of the dynamic nature of Python, some warnings may be incorrect; however, spurious warnings should be fairly infrequent.

**Pros**

Catches easy-to-miss errors like typos, using-vars-before-assignment, etc.

**Cons**

**pylint** isn’t perfect. To take advantage of it, sometimes developers will need to write around it, suppress its warnings or fix it.

**Decision**

Make sure to run pylint on the code. Suppress warnings if they are inappropriate so that other issues are not hidden. To suppress warnings, we can set a line-level comment:

**def** **do\_PUT**(self):  *\# WSGI name, so pylint: disable=invalid-name*  
  ...  
pylint warnings are each identified by symbolic name (empty-docstring). If the reason for the suppression is not clear from the symbolic name, add an explanation. Suppressing in this way has the advantage that we can easily search for suppressions and revisit them.

You can get a list of pylint warnings by doing:

pylint \--list-msgs

To get more information on a particular message, use:

`pylint` `--help-msg=invalid-name`  
Prefer pylint: disable to the deprecated older form pylint: disable-msg.

Unused argument warnings can be suppressed by deleting the variables at the beginning of the function. Always include a comment explaining why you are deleting it. “Unused.” is sufficient. For example:

**def** **viking\_cafe\_order**(spam: str, beans: str, eggs: str **|** None **\=** None) **\-\>** str:  
    **del** beans, eggs  *\# Unused by vikings.*  
    **return** spam **\+** spam **\+** spam  
Other common forms of suppressing this warning include using ‘\_’ as the identifier for the unused argument or prefixing the argument name with ‘unused\_’, or assigning them to ‘\_’. These forms are allowed but no longer encouraged. These break callers that pass arguments by name and do not enforce that the arguments are actually unused.

2. #### Imports

     
   Use import statements for packages and modules only, not for individual classes or functions. Reusability mechanism for sharing code from one module to another.

**Pros**

The namespace management convention is simple. The source of each identifier is indicated in a consistent way; **x.Obj** says that object **Obj** is defined in module **x**.

#### Cons

Module names can still collide. Some module names are inconveniently long.

**Decision**

* Use **import x** for importing packages and modules.  
* Use **from x import y** where **x** is the package prefix and **y** is the module name with no prefix.  
* Use **from x import y as z** in any of the following circumstances:  
  * Two modules named y are to be imported.  
  * y conflicts with a top-level name defined in the current module.  
  * y conflicts with a common parameter name that is part of the public API (e.g., features).  
  * y is an inconveniently long name.  
  * y is too generic in the context of your code (e.g., from storage.file\_system import options as fs\_options).  
* Use **import y as z** only when z is a standard abbreviation (e.g., import numpy as np).

  For example the module sound.effects.echo may be imported as follows:

  **from** sound.effects **import** echo

  ...

  echo.EchoFilter(input, output, delay**\=**0.7, atten**\=**4)

  Do not use relative names in imports. Even if the module is in the same package, use the full package name. This helps prevent unintentionally importing a package twice.

**Exemptions**

Exemptions from this rule:

* Symbols from the following modules are used to support static analysis and type checking:  
  * [typing module](https://google.github.io/styleguide/pyguide.html#typing-imports)  
  * [collections.abc module](https://google.github.io/styleguide/pyguide.html#typing-imports)  
  * [typing\_extensions module](https://github.com/python/typing_extensions/blob/main/README.md)  
* Redirects from the [six.moves module](https://six.readthedocs.io/#module-six.moves).


3. #### Packages

     
   Import each module using the full pathname location of the module.

**Pros**

Avoids conflicts in module names or incorrect imports due to the module search path not being what the author expected. Makes it easier to find modules.

**Cons**

Makes it harder to deploy code because you have to replicate the package hierarchy. Not really a problem with modern deployment mechanisms.

**Decision**

All new code should import each module by its full package name.  
Imports should be as follows:  
Yes:

  *\# Reference absl.flags in code with the complete name (verbose).*

  **import** absl.flags

  **from** doctor.who **import** jodie

  \_FOO **\=** absl.flags.DEFINE\_string(...)

`Yes:`

  *\# Reference flags in code with just the module name (common).*

  **from** absl **import** flags

  **from** doctor.who **import** jodie

  \_FOO **\=** flags.DEFINE\_string(...)

*(assume this file lives in doctor/who/ where jodie.py also exists)*  
No:

  *\# Unclear what module the author wanted and what will be imported.  The actual*

  *\# import behavior depends on external factors controlling sys.path.*

  *\# Which possible jodie module did the author intend to import?*

  **import** jodie

The directory the main binary is located in should not be assumed to be in sys.path despite that happening in some environments. This being the case, code should assume that import jodie refers to a third-party or top-level package named jodie, not a local jodie.py.

4. #### Exceptions

     
   Exceptions are a means of breaking out of normal control flow to handle errors or other exceptional conditions. Exceptions are allowed but must be used carefully.

**Pros**

The control flow of normal operation code is not cluttered by error-handling code. It also allows the control flow to skip multiple frames when a certain condition occurs, e.g., returning from N nested functions in one step instead of having to plumb error codes through.

**Cons**

May cause the control flow to be confusing. Easy to miss error cases when making library calls.

**Decision**

* Make use of built-in exception classes when it makes sense. For example, raise a ValueError to indicate a programming mistake like a violated precondition (such as if you were passed a negative number but required a positive one). Do not use assert statements for validating argument values of a public API. assert is used to ensure internal correctness, not to enforce correct usage nor to indicate that some unexpected event occurred. If an exception is desired in the latter cases, use a raise statement. For example:


  Yes:

    **def** **connect\_to\_next\_port**(self, minimum: int) **\-\>** int:

      """Connects to the next available port.


      Args:

        minimum: A port value greater or equal to 1024\.


      Returns:

        The new minimum port.


      Raises:

        ConnectionError: If no available port is found.

      """

      **if** minimum **\<** 1024:

        *\# Note that this raising of ValueError is not mentioned in the doc*

        *\# string's "Raises:" section because it is not appropriate to*

        *\# guarantee this specific behavioral reaction to API misuse.*

        **raise** ValueError(f'Min. port must be at least 1024, not {minimum}.')

      port **\=** self.\_find\_next\_open\_port(minimum)

      **if** port **is** None:

        **raise** ConnectionError(

            f'Could not connect to service on port {minimum} or higher.')

      **assert** port **\>=** minimum, (

          f'Unexpected port {port} when minimum was {minimum}.')

      **return** port

  No:

    **def** **connect\_to\_next\_port**(self, minimum: int) **\-\>** int:

      """Connects to the next available port.


      Args:

        minimum: A port value greater or equal to 1024\.


      Returns:

        The new minimum port.

      """

      **assert** minimum **\>=** 1024, 'Minimum port must be at least 1024.'

      port **\=** self.\_find\_next\_open\_port(minimum)

      **assert** port **is** **not** None

      **return** port


* Libraries or packages may define their own exceptions. When doing so they must inherit from an existing exception class. Exception names should end in Error and should not introduce repetition (foo.FooError).

* Never use catch-all except: statements, or catch Exception or StandardError, unless you are  
  * re-raising the exception, or  
  * creating an isolation point in the program where exceptions are not propagated but are recorded and suppressed, such as protecting a thread from crashing by guarding its outermost block.  
* Python is very tolerant in this regard and except: will really catch everything including misspelled names, sys.exit() calls, Ctrl+C interrupts, unittest failures, and all kinds of other exceptions that you simply don’t want to catch.

* Minimize the amount of code in a try/except block. The larger the body of the try, the more likely that an exception will be raised by a line of code that you didn’t expect to raise an exception. In those cases, the try/except block hides a real error.

* Use the finally clause to execute code whether or not an exception is raised in the try block. This is often useful for cleanup, i.e., closing a file.

5. #### Mutable Global State

     
   Module-level values or class attributes that can get mutated during program execution.Avoid mutable global state.  
     
   **Pros**  
     
   Occasionally useful.

#### Cons

* Breaks encapsulation: Such design can make it hard to achieve valid objectives. For example, if the global state is used to manage a database connection, then connecting to two different databases at the same time (such as for computing differences during a migration) becomes difficult. Similar problems easily arise with global registries.

* Has the potential to change module behavior during the import, because assignments to global variables are done when the module is first imported.

#### Decision

In those rare cases where using global state is warranted, mutable global entities should be declared at the module level or as a class attribute and made internal by prepending an \_ to the name. If necessary, external access to mutable global state must be done through public functions or class methods. See Naming below. Please explain the design reasons why mutable global state is being used in a comment or a doc linked to from a comment.  
Module-level constants are permitted and encouraged. 

For example: \_MAX\_HOLY\_HANDGRENADE\_COUNT \= 3 for an internal use constant or SIR\_LANCELOTS\_FAVORITE\_COLOR \= "blue" for a public API constant. Constants must be named using all caps with underscores. 

6. #### Nested/Local/Inner Classes and Functions

     
   A class can be defined inside of a method, function, or class. A function can be defined inside a method or function. Nested functions have read-only access to variables defined in enclosing scopes. Nested local functions or classes are fine when used to close over a local variable. Inner classes are fine.

**Pros**

Allows definition of utility classes and functions that are only used inside of a very limited scope. Commonly used for implementing decorators.

#### Cons

Nested functions and classes cannot be directly tested. Nesting can make the outer function longer and less readable.

#### Decision

They are fine with some caveats. Avoid nested functions or classes except when closing over a local value other than self or cls. Do not nest a function just to hide it from users of a module. Instead, prefix its name with an \_ at the module level so that it can still be accessed by tests.

7. #### Comprehensions & Generator Expressions

     
   List, Dict, and Set comprehensions as well as generator expressions provide a concise and efficient way to create container types and iterators without resorting to the use of traditional loops, map(), filter(), or lambda.

**Pros**

Simple comprehensions can be clearer and simpler than other dict, list, or set creation techniques. Generator expressions can be very efficient, since they avoid the creation of a list entirely.

**Cons**

Complicated comprehensions or generator expressions can be hard to read.

**Decision**

Okay to use for simple cases. Each portion must fit on one line: mapping expression, for clause, filter expression. Multiple for clauses or filter expressions are not permitted. Use loops instead when things get more complicated.

Yes:  
  result **\=** \[mapping\_expr **for** value **in** iterable **if** filter\_expr\]

  result **\=** \[{'key': value} **for** value **in** iterable  
            **if** a\_long\_filter\_expression(value)\]

  result **\=** \[complicated\_transform(x)  
            **for** x **in** iterable **if** predicate(x)\]

  descriptive\_name **\=** \[  
      transform({'key': key, 'value': value}, color**\=**'black')  
      **for** key, value **in** generate\_iterable(some\_input)  
      **if** complicated\_condition\_is\_met(key, value)  
  \]

  result **\=** \[\]  
  **for** x **in** range(10):  
      **for** y **in** range(5):  
          **if** x **\*** y **\>** 10:  
              result.append((x, y))

  **return** {x: complicated\_transform(x)  
          **for** x **in** long\_generator\_function(parameter)  
          **if** x **is** **not** None}

  squares\_generator **\=** (x**\*\***2 **for** x **in** range(10))

  unique\_names **\=** {user.name **for** user **in** users **if** user **is** **not** None}

  eat(jelly\_bean **for** jelly\_bean **in** jelly\_beans  
      **if** jelly\_bean.color **\==** 'black')

No:  
  result **\=** \[complicated\_transform(  
                x, some\_argument**\=**x**\+**1)  
            **for** x **in** iterable **if** predicate(x)\]

  result **\=** \[(x, y) **for** x **in** range(10) **for** y **in** range(5) **if** x **\*** y **\>** 10\]

  **return** ((x, y, z)  
          **for** x **in** range(5)  
          **for** y **in** range(5)  
          **if** x **\!=** y  
          **for** z **in** range(5)  
          **if** y **\!=** z)

 

8. #### Default Iterators and Operators

     
   Container types, like dictionaries and lists, define default iterators and membership test operators (“in” and “not in”). Use default iterators and operators for types that support them, like lists, dictionaries, and files.

**Pros**

The default iterators and operators are simple and efficient. They express the operation directly, without extra method calls. A function that uses default operators is generic. It can be used with any type that supports the operation.

**Cons**

You can’t tell the type of objects by reading the method names (unless the variable has type annotations). This is also an advantage.

**Decision**

Use default iterators and operators for types that support them, like lists, dictionaries, and files. The built-in types define iterator methods, too. Prefer these methods to methods that return lists, except that you should not mutate a container while iterating over it.

Yes:  **for** key **in** adict: ...  
      **if** obj **in** alist: ...  
      **for** line **in** afile: ...  
      **for** k, v **in** adict.items(): ...

No:   **for** key **in** adict.keys(): ...  
      **for** line **in** afile.readlines(): ...

9. #### Generators

     
     
   A generator function returns an iterator that yields a value each time it executes a yield statement. After it yields a value, the runtime state of the generator function is suspended until the next value is needed.

**Pros**

Simpler code, because the state of local variables and control flow are preserved for each call. A generator uses less memory than a function that creates an entire list of values at once.

**Cons**

Local variables in the generator will not be garbage collected until the generator is either consumed to exhaustion or itself garbage collected.

**Decision**

Use “Yields:” rather than “Returns:” in the docstring for generator functions.  
If the generator manages an expensive resource, make sure to force the clean-up.  
A good way to do the cleanup is by wrapping the generator with a context manager, [PEP-0533](https://peps.python.org/pep-0533/).

10. #### Lambda Functions

      
    Lambdas defines anonymous functions in an expression, as opposed to a statement.

**Pros**

Convenient

**Cons**

Harder to read and debug than local functions. The lack of names means stack traces are more difficult to understand. Expressiveness is limited because the function may only contain an expression.

**Decision**

Okay to use them for one-liners. If the code inside the lambda function is longer than 60-80 chars, it’s probably better to define it as a regular [nested function](https://google.github.io/styleguide/pyguide.html#lexical-scoping).

For common operations like multiplication, use the functions from the operator module instead of lambda functions.   
For example, prefer **operator.mul** to **lambda x, y: x \* y**

11. #### Conditional Expressions

      
    Conditional expressions (sometimes called a “ternary operator”) are mechanisms that provide a shorter syntax for if statements.   
    For example: x \= 1 if cond else 2\.

**Pros**

Shorter and more convenient than an if statement.

**Cons**

May be harder to read than an if statement. The condition may be difficult to locate if the expression is long.

**Decision**

Okay to use for simple cases. Each portion must fit on one line: true-expression, if-expression, else-expression. Use a complete if statement when things get more complicated.

12. #### Default Argument Values

    You can specify values for variables at the end of a function’s parameter list, e.g., def foo(a, b=0):. If foo is called with only one argument, b is set to 0\. If it is called with two arguments, b has the value of the second argument.

**Pros**

Often you have a function that uses lots of default values, but on rare occasions you want to override the defaults. Default argument values provide an easy way to do this, without having to define lots of functions for the rare exceptions. As Python does not support overloaded methods/functions, default arguments are an easy way of “faking” the overloading behavior.

**Cons**

Default arguments are evaluated once at module load time. This may cause problems if the argument is a mutable object such as a list or a dictionary. If the function modifies the object (e.g., by appending an item to a list), the default value is modified.

**Decision**

Okay, to use with the following caveat:  
Do not use mutable objects as default values in the function or method definition.

Yes: 

**def** **foo**(a, b**\=**None):  
         **if** b **is** None:  
             b **\=** \[\]  
Yes: **def** **foo**(a, b: Sequence **|** None **\=** None):  
         **if** b **is** None:  
             b **\=** \[\]  
Yes: **def** **foo**(a, b: Sequence **\=** ()):  *\# Empty tuple OK since tuples are immutable.*  
         ...

**from** absl **import** flags  
\_FOO **\=** flags.DEFINE\_string(...)

No:  **def** **foo**(a, b**\=**\[\]):  
         ...  
No:  **def** **foo**(a, b**\=**time.time()):  *\# The time the module was loaded???*  
         ...  
No:  **def** **foo**(a, b**\=**\_FOO.value):  *\# sys.argv has not yet been parsed...*  
         ...  
No:  **def** **foo**(a, b: Mapping **\=** {}):  *\# Could still get passed to unchecked code.*  
         ...

Yes:

    one\_line **\=** 'yes' **if** predicate(value) **else** 'no'

    slightly\_split **\=** ('yes' **if** predicate(value)

                      **else** 'no, nein, nyet')

    the\_longest\_ternary\_style\_that\_can\_be\_done **\=** (

        'yes, true, affirmative, confirmed, correct'

        **if** predicate(value)

        **else** 'no, false, negative, nay')

No:

    bad\_line\_breaking **\=** ('yes' **if** predicate(value) **else**

                         'no')

    portion\_too\_long **\=** ('yes'

                        **if** some\_long\_module.some\_long\_predicate\_function(

                            really\_long\_variable\_name)

                        **else** 'no, false, negative, nay')

13. #### Properties {#properties}

    A way to wrap method calls for getting and setting an attribute as standard attribute access.

    

    Properties may be used to control getting or setting attributes that require trivial computations or logic. Property implementations must match the general expectations of regular attribute access: that they are cheap, straightforward, and unsurprising.

**Pros**

* Allows for an attribute access and assignment API rather than [getter and setter](https://google.github.io/styleguide/pyguide.html#getters-and-setters) method calls.  
* Can be used to make an attribute read-only.  
* Allows calculations to be lazy.  
* Provides a way to maintain the public interface of a class when the internals evolve independently of class users.

**Cons**

* Can hide side effects much like operator overloading.  
* Can be confusing for subclasses.

**Decision**

Properties are allowed, but, like operator overloading, should only be used when necessary and match the expectations of typical attribute access; follow the [getters and setters](https://google.github.io/styleguide/pyguide.html#getters-and-setters) rules otherwise.

For example, using a property to simply both get and set an internal attribute isn’t allowed: there is no computation occurring, so the property is unnecessary ([make the attribute public instead](https://google.github.io/styleguide/pyguide.html#getters-and-setters)). In comparison, using a property to control attribute access or to calculate a trivially derived value is allowed: the logic is simple and unsurprising.  
Properties should be created with the @property [decorator](https://google.github.io/styleguide/pyguide.html#s2.17-function-and-method-decorators). Manually implementing a property descriptor is considered a [power feature](https://google.github.io/styleguide/pyguide.html#power-features).  
Inheritance with properties can be non-obvious. Do not use properties to implement computations a subclass may ever want to override and extend.

14. #### True/False Evaluations

    Python evaluates certain values as False when in a boolean context. A quick “rule of thumb” is that all “empty” values are considered false, so 0, None, \[\], {}, '' all evaluate as false in a boolean context. Use the “implicit” false if at all possible (with a few caveats).

**Pros**

Conditions using Python booleans are easier to read and less error-prone. In most cases, they’re also faster.

**Cons**

May look strange to C/C++ developers.

**Decision**

Use the “implicit” false if possible, e.g., if foo: rather than if foo \!= \[\]:. There are a few caveats that you should keep in mind though:

* Always use if foo is None: (or is not None) to check for a None value. E.g., when testing whether a variable or argument that defaults to None was set to some other value. The other value might be a value that’s false in a boolean context\!  
* Never compare a boolean variable to False using \==. Use if not x: instead. If you need to distinguish False from None then chain the expressions, such as if not x and x is not None:.  
* For sequences (strings, lists, tuples), use the fact that empty sequences are false, so if seq: and if not seq: are preferable to if len(seq): and if not len(seq): respectively.  
* When handling integers, implicit false may involve more risk than benefit (i.e., accidentally handling None as 0). You may compare a value that is known to be an integer (and is not the result of len()) against the integer 0\.  
    
    
  Yes: **if** **not** users:

           **print**('no users')


       **if** i **%** 10 **\==** 0:

           self.handle\_multiple\_of\_ten()


       **def** **f**(x**\=**None):

           **if** x **is** None:

               x **\=** \[\]

    
  No:  **if** len(users) **\==** 0:

           **print**('no users')


       **if** **not** i **%** 10:

           self.handle\_multiple\_of\_ten()


       **def** **f**(x**\=**None):

           x **\=** x **or** \[\]

* Note that '0' (i.e., 0 as string) evaluates to true.  
* Note that Numpy arrays may raise an exception in an implicit boolean context. Prefer the .size attribute when testing the emptiness of a np.array (e.g. if not users.size).


15. #### Lexical Scoping

    A nested Python function can refer to variables defined in enclosing functions, but cannot assign to them. Variable bindings are resolved using lexical scoping, that is, based on the static program text. Any assignment to a name in a block will cause Python to treat all references to that name as a local variable, even if the use precedes the assignment. If a global declaration occurs, the name is treated as a global variable.

    An example of the use of this feature is:

    **def** **get\_adder**(summand1: float) **\-\>** Callable\[\[float\], float\]:

        """Returns a function that adds numbers to a given number."""

        **def** **adder**(summand2: float) **\-\>** float:

            **return** summand1 **\+** summand2

    

        **return** adder

**Pros**

Often results in clearer, more elegant code. Especially comforting to experienced Lisp and Scheme (and Haskell and ML and …) programmers.

**Cons**

This can lead to confusing bugs, such as this example based on [PEP-0227](https://peps.python.org/pep-0227/):

i **\=** 4

**def** **foo**(x: Iterable\[int\]):

    **def** **bar**():

        **print**(i, end**\=**'')

    *\# ...*

    *\# A bunch of code here*

    *\# ...*

    **for** i **in** x:  *\# Ah, i \*is\* local to foo, so this is what bar sees*

        **print**(i, end**\=**'')

    bar()

So foo(\[1, 2, 3\]) will print 1 2 3 3, not 1 2 3 4\.

**Decision**

Okay to use.

16. #### Function and Method Decorators

      
    [Decorators for Functions and Methods](https://docs.python.org/3/glossary.html#term-decorator) (a.k.a “the @ notation”). One common decorator is @property, used for converting ordinary methods into dynamically computed attributes. Use decorators judiciously when there is a clear advantage. Avoid staticmethod and limit use of classmethod.  
      
    However, the decorator syntax allows for user-defined decorators as well. Specifically, for some function my\_decorator, this:

**class** **C**:

    **@**my\_decorator

    **def** **method**(self):

        *\# method body ...*

is equivalent to:  
**class** **C**:

    **def** **method**(self):

        *\# method body ...*

    method **\=** my\_decorator(method)

**Pros**

Elegantly specifies some transformation on a method; the transformation might eliminate some repetitive code, enforce invariants, etc.

**Cons**

Decorators can perform arbitrary operations on a function’s arguments or return values, resulting in surprising implicit behavior. Additionally, decorators execute at object definition time. For module-level objects (classes, module functions, …) this happens at import time. Failures in decorator code are pretty much impossible to recover from.

**Decision**

Use decorators judiciously when there is a clear advantage. Decorators should follow the same import and naming guidelines as functions. Decorator pydoc should clearly state that the function is a decorator. Write unit tests for decorators.

Avoid external dependencies in the decorator itself (e.g. don’t rely on files, sockets, database connections, etc.), since they might not be available when the decorator runs (at import time, perhaps from pydoc or other tools). A decorator that is called with valid parameters should (as much as possible) be guaranteed to succeed in all cases.  
Decorators are a special case of “top-level code” .  
Never use staticmethod unless forced to in order to integrate with an API defined in an existing library. Write a module-level function instead.

Use classmethod only when writing a named constructor, or a class-specific routine that modifies necessary global state such as a process-wide cache.

17. #### Threading

      
    Do not rely on the atomicity of built-in types.  
      
    While Python’s built-in data types such as dictionaries appear to have atomic operations, there are corner cases where they aren’t atomic (e.g. if \_\_hash\_\_ or \_\_eq\_\_ are implemented as Python methods) and their atomicity should not be relied upon. Neither should you rely on atomic variable assignment (since this in turn depends on dictionaries).  
      
    Use the queue module’s Queue data type as the preferred way to communicate data between threads. Otherwise, use the threading module and its locking primitives. Prefer condition variables and threading. Condition instead of using lower-level locks.

18. #### Power Features

      
    Python is an extremely flexible language and gives you many fancy features such as custom metaclasses, access to bytecode, on-the-fly compilation, dynamic inheritance, object reparenting, import hacks, reflection (e.g. some uses of getattr()), modification of system internals, \_\_del\_\_ methods implementing customized cleanup, etc.  
      
    Avoid these features.

**Pros**

These are powerful language features. They can make your code more compact.

**Cons**

It’s very tempting to use these “cool” features when they’re not absolutely necessary. It’s harder to read, understand, and debug code that’s using unusual features underneath. It doesn’t seem that way at first (to the original author), but when revisiting the code, it tends to be more difficult than code that is longer but is straightforward.

**Decision**

Avoid these features in your code.

Standard library modules and classes that internally use these features are okay to use (for example, abc.ABCMeta, dataclasses, and enum).

19. #### Modern Python: from \_\_future\_\_ imports

      
    Being able to turn on some of the more modern features via from \_\_future\_\_ import statements allows early use of features from expected future Python versions.  
    New language version semantic changes may be gated behind a special future import to enable them on a per-file basis within earlier runtimes.

**Pros**

This has proven to make runtime version upgrades smoother as changes can be made on a per-file basis while declaring compatibility and preventing regressions within those files. Modern code is more maintainable as it is less likely to accumulate technical debt that will be problematic during future runtime upgrades.

**Cons**

Such code may not work on very old interpreter versions prior to the introduction of the needed future statement. The need for this is more common in projects supporting an extremely wide variety of environments.

**Decision**

**from \_\_future\_\_ imports**

Use of from \_\_future\_\_ import statements is encouraged. It allows a given source file to start using more modern Python syntax features today. Once you no longer need to run on a version where the features are hidden behind a \_\_future\_\_ import, feel free to remove those lines.  
In code that may execute on versions as old as 3.5 rather than \>= 3.7, import:

**from** \_\_future\_\_ **import** generator\_stop

For more information read the [Python future statement definitions](https://docs.python.org/3/library/__future__.html) documentation.  
Please don’t remove these imports until you are confident the code is only ever used in a sufficiently modern environment. Even if you do not currently use the feature a specific future import enables in your code today, keeping it in place in the file prevents later modifications of the code from inadvertently depending on the older behavior.

Use other **from \_\_future\_\_ import** statements as you see fit.

20. #### Type Annotated Code

      
    Type annotations (or “type hints”) are for function or method arguments and return values:  
    

**def** **func**(a: int) **\-\>** list\[int\]:  
You can also declare the type of a variable using similar [PEP-526](https://peps.python.org/pep-0526/) syntax:

a: SomeType **\=** some\_func()

You can annotate Python code with type hints according to PEP-484, and type-check the code at build time with a type checking tool like pytype.

Type annotations can be in the source or in a stub pyi file. Whenever possible, annotations should be in the source. Use pyi files for third-party or extension modules.

**Pros**

Type annotations improve the readability and maintainability of your code. The type checker will convert many runtime errors to build-time errors, and reduce your ability to use [Power Features](https://google.github.io/styleguide/pyguide.html#power-features).

**Cons**

You will have to keep the type declarations up to date. You might see type errors that you think are valid code. Use of a [type checker](https://github.com/google/pytype) may reduce your ability to use [Power Features](https://google.github.io/styleguide/pyguide.html#power-features).

**Decision**

You are strongly encouraged to enable Python-type analysis when updating code. When adding or modifying public APIs, include type annotations and enable checking via pytype in the build system. As static analysis is relatively new to Python, we acknowledge that undesired side-effects (such as wrongly inferred types) may prevent adoption by some projects. In those situations, authors are encouraged to add a comment with a TODO or link to a bug describing the issue(s) currently preventing type annotation adoption in the BUILD file or in the code itself as appropriate.

### **Python Style Rules** {#python-style-rules}

1. #### Semicolons

     
   Do not terminate your lines with semicolons, and do not use semicolons to put two statements on the same line.

2. #### Line length {#line-length-1}

     
   Maximum line length is 80 characters.  
     
   Explicit exceptions to the 80 character limit:  
     
* Long import statements.  
* URLs, pathnames, or long flags in comments.  
* Long string module-level constants not containing whitespace that would be inconvenient to split across lines such as URLs or pathnames.  
  * Pylint disable comments. (e.g.: \# pylint: disable=invalid-name)

  Do not use a backslash for explicit line continuation.


  Instead, make use of Python’s implicit line joining inside parentheses, brackets and braces. If necessary, you can add an extra pair of parentheses around an expression.


  Note that this rule doesn’t prohibit backslash-escaped newlines within strings.


  Yes: foo\_bar(self, width, height, color**\=**'black', design**\=**None, x**\=**'foo',

               emphasis**\=**None, highlight**\=**0)

Yes: **if** (width **\==** 0 **and** height **\==** 0 **and**  
         color **\==** 'red' **and** emphasis **\==** 'strong'):

     (bridge\_questions.clarification\_on  
      .average\_airspeed\_of.unladen\_swallow) **\=** 'African or European?'

     **with** (  
         very\_long\_first\_expression\_function() **as** spam,  
         very\_long\_second\_expression\_function() **as** beans,  
         third\_thing() **as** eggs,  
     ):  
       place\_order(eggs, beans, spam, beans)

No:  **if** width **\==** 0 **and** height **\==** 0 **and** \\  
         color **\==** 'red' **and** emphasis **\==** 'strong':

     bridge\_questions.clarification\_on \\  
         .average\_airspeed\_of.unladen\_swallow **\=** 'African or European?'

     **with** very\_long\_first\_expression\_function() **as** spam, \\  
           very\_long\_second\_expression\_function() **as** beans, \\  
           third\_thing() **as** eggs:  
       place\_order(eggs, beans, spam, beans)

When a literal string won’t fit on a single line, use parentheses for implicit line joining.

x **\=** ('This will build a very long long '  
     'long long long long long long string')

Prefer to break lines at the highest possible syntactic level. If you must break a line twice, break it at the same syntactic level both times.

Yes: bridgekeeper.answer(  
         name**\=**"Arthur", quest**\=**questlib.find(owner**\=**"Arthur", perilous**\=**True))

     answer **\=** (a\_long\_line().of\_chained\_methods()  
               .that\_eventually\_provides().an\_answer())

     **if** (  
         config **is** None  
         **or** 'editor.language' **not** **in** config  
         **or** config\['editor.language'\].use\_spaces **is** False  
     ):  
       use\_tabs()

No: bridgekeeper.answer(name**\=**"Arthur", quest**\=**questlib.find(  
        owner**\=**"Arthur", perilous**\=**True))

    answer **\=** a\_long\_line().of\_chained\_methods().that\_eventually\_provides(  
        ).an\_answer()

    **if** (config **is** None **or** 'editor.language' **not** **in** config **or** config\[  
        'editor.language'\].use\_spaces **is** False):  
      use\_tabs()

Within comments, put long URLs on their own line if necessary.

`Yes:`  *\# See details at*  
      *\# http://www.example.com/us/developer/documentation/api/content/v2.0/csv\_file\_name\_extension\_full\_specification.html*

*No:  \# See details at*  
     *\# http://www.example.com/us/developer/documentation/api/content/\\*  
     *\# v2.0/csv\_file\_name\_extension\_full\_specification.html*

Make note of the indentation of the elements in the line continuation examples above; see the indentation section for explanation.

In all other cases where a line exceeds 80 characters, and the [Black](https://github.com/psf/black) or [Pyink](https://github.com/google/pyink) auto-formatter does not help bring the line below the limit, the line is allowed to exceed this maximum. Authors are encouraged to manually break the line up per the notes above when it is sensible.

3. #### Parentheses

     
   Use parentheses sparingly.  
     
   It is fine, though not required, to use parentheses around tuples. Do not use them in return statements or conditional statements unless using parentheses for implied line continuation or to indicate a tuple.  
     
   Yes: **if** foo:  
            bar()  
        **while** x:  
            x **\=** bar()  
        **if** x **and** y:  
            bar()  
        **if** **not** x:  
            bar()  
        *\# For a 1 item tuple the ()s are more visually obvious than the comma.*  
        onesie **\=** (foo,)  
        **return** foo  
        **return** spam, beans  
        **return** (spam, beans)  
        **for** (x, y) **in** dict.items(): ...  
     
   No:  **if** (x):  
            bar()  
        **if** **not**(x):  
            bar()  
        **return** (foo)  
   

4. #### Indentation {#indentation-1}

     
   Indent your code blocks with 4 spaces.  
   Never use tabs. Implied line continuation should align wrapped elements vertically or use a hanging 4-space indent. Closing (round, square or curly) brackets can be placed at the end of the expression, or on separate lines, but then should be indented the same as the line with the corresponding opening bracket.

   Yes:   *\# Aligned with opening delimiter.*

          foo **\=** long\_function\_name(var\_one, var\_two,

                                   var\_three, var\_four)

          meal **\=** (spam,

                  beans)

   

          *\# Aligned with opening delimiter in a dictionary.*

          foo **\=** {

              'long\_dictionary\_key': value1 **\+**

                                     value2,

              ...

          }

   

          *\# 4-space hanging indent; nothing on first line.*

          foo **\=** long\_function\_name(

              var\_one, var\_two, var\_three,

              var\_four)

          meal **\=** (

              spam,

              beans)

   

          *\# 4-space hanging indent; nothing on first line,*

          *\# closing parenthesis on a new line.*

          foo **\=** long\_function\_name(

              var\_one, var\_two, var\_three,

              var\_four

          )

          meal **\=** (

              spam,

              beans,

          )

   

          *\# 4-space hanging indent in a dictionary.*

          foo **\=** {

              'long\_dictionary\_key':

                  long\_dictionary\_value,

              ...

          }

#### 

   No:    *\# Stuff on first line forbidden.*

          foo **\=** long\_function\_name(var\_one, var\_two,

              var\_three, var\_four)

          meal **\=** (spam,

              beans)

   

          *\# 2-space hanging indent forbidden.*

          foo **\=** long\_function\_name(

            var\_one, var\_two, var\_three,

            var\_four)

   

          *\# No hanging indent in a dictionary.*

          foo **\=** {

              'long\_dictionary\_key':

              long\_dictionary\_value,

              ...

          }

#### 

   1. ##### Trailing commas in sequences of items?

      Trailing commas in sequences of items are recommended only when the closing container token \], ), or } does not appear on the same line as the final element, as well as for tuples with a single element. The presence of a trailing comma is also used as a hint to our Python code auto-formatted

5. #### Shebang Line

     
   Most  .py  files do not need to start with a  \#\!  line. Start the main file of a program with       \#\!/usr/bin/env python3  (to support virtualenvs) or  \#\!/usr/bin/python3  per [PEP-394](https://peps.python.org/pep-0394/).  
     
   This line is used by the kernel to find the Python interpreter, but is ignored by Python when importing modules. It is only necessary on a file intended to be executed directly.  
   

6. #### Comments and Docstrings

     
   Be sure to use the right style for module, function, method docstrings and inline comments.

   1. ##### Docstrings

      Python uses docstrings to document code. A docstring is a string that is the first statement in a package, module, class or function. These strings can be extracted automatically through the  \_\_doc\_\_  member of the object and are used by  pydoc . (Try running  pydoc  on your module to see how it looks.) Always use the three-double-quote  """  format for docstrings (per [PEP 257](https://peps.python.org/pep-0257/)). A docstring should be organized as a summary line (one physical line not exceeding 80 characters) terminated by a period, question mark, or exclamation point. When writing more (encouraged), this must be followed by a blank line, followed by the rest of the docstring starting at the same cursor position as the first quote of the first line. There are more formatting guidelines for docstrings below.

   2. ##### Modules

      Every file should contain license boilerplate. Choose the appropriate boilerplate for the license used by the project (for example, Apache 2.0, BSD, LGPL, GPL).  
        
      Files should start with a docstring describing the contents and usage of the module.  
        
      """A one-line summary of the module or program, terminated by a period.  
        
      Leave one blank line.  The rest of this docstring should contain an  
      overall description of the module or program.  Optionally, it may also  
      contain a brief description of exported classes and functions and/or usage  
      examples.  
        
      Typical usage example:  
        
        foo \= ClassFoo()  
        bar \= foo.FunctionBar()  
      """  
      

      1. ###### *Test modules*

           
         Module-level docstrings for test files are not required. They should be included only when there is additional information that can be provided.  
           
         Examples include some specifics on how the test should be run, an explanation of an unusual setup pattern, dependency on the external environment, and so on.  
         

      """This blaze test uses golden files.  
        
      You can update those files by running  
      \`blaze run //foo/bar:foo\_test \-- \--update\_golden\_files\` from the \`google3\`  
      directory.  
      """

           
         Docstrings that do not provide any new information should not be used.  
         

   """Tests for foo.bar."""

         

   3. ##### Functions and Methods

      In this section, “function” means a method, function, generator, or property.  
        
      A docstring is mandatory for every function that has one or more of the following properties:  
        
* being part of the public API  
* nontrivial size  
* non-obvious logic


  A docstring should give enough information to write a call to the function without reading the function’s code. The docstring should describe the function’s calling syntax and its semantics, but generally not its implementation details, unless those details are relevant to how the function is to be used. For example, a function that mutates one of its arguments as a side effect should note that in its docstring. Otherwise, subtle but important details of a function’s implementation that are not relevant to the caller are better expressed as comments alongside the code than within the function’s docstring.


  The docstring may be descriptive-style ( """Fetches rows from a Bigtable.""" ) or imperative-style ( """Fetch rows from a Bigtable.""" ), but the style should be consistent within a file. The docstring for a @property data descriptor should use the same style as the docstring for an attribute or a [function argument](#heading=h.gk4gqmiro98k) ( """The Bigtable path.""" , rather than  """Returns the Bigtable path.""" ).


  A method that overrides a method from a base class may have a simple docstring sending the reader to its overridden method’s docstring, such as  """See base class.""" . The rationale is that there is no need to repeat in many places documentation that is already present in the base method’s docstring. However, if the overriding method’s behavior is substantially different from the overridden method, or details need to be provided (e.g., documenting additional side effects), a docstring with at least those differences is required on the overriding method.


  Certain aspects of a function should be documented in special sections, listed below. Each section begins with a heading line, which ends with a colon. All sections other than the heading should maintain a hanging indent of two or four spaces (be consistent within a file). These sections can be omitted in cases where the function’s name and signature are informative enough that it can be aptly described using a one-line docstring.

  **Args:**

  List each parameter by name. A description should follow the name, and be separated by a colon followed by either a space or newline. If the description is too long to fit on a single 80-character line, use a hanging indent of 2 or 4 spaces more than the parameter name (be consistent with the rest of the docstrings in the file). The description should include required type(s) if the code does not contain a corresponding type annotation. If a function accepts  \*foo  (variable length argument lists) and/or  \*\*bar  (arbitrary keyword arguments), they should be listed as  \*foo  and  \*\*bar .

  **Returns: (or Yields: for generators)**

  Describe the semantics of the return value, including any type information that the type annotation does not provide. If the function only returns None, this section is not required. It may also be omitted if the docstring starts with Returns or Yields (e.g.  """Returns row from Bigtable as a tuple of strings.""" ) and the opening sentence is sufficient to describe the return value. Do not imitate older ‘NumPy style’ ([example](https://numpy.org/doc/1.24/reference/generated/numpy.linalg.qr.html)), which frequently documented a tuple return value as if it were multiple return values with individual names (never mentioning the tuple). Instead, describe such a return value as: “Returns: A tuple (mat\_a, mat\_b), where mat\_a is …, and …”. The auxiliary names in the docstring need not necessarily correspond to any internal names used in the function body (as those are not part of the API).

  **Raises:**

  List all exceptions that are relevant to the interface followed by a description. Use a similar exception name \+ colon \+ space or newline and hanging indent style as described in [Args:](#heading=h.gk4gqmiro98k). You should not document exceptions that get raised if the API specified in the docstring is violated (because this would paradoxically make behavior under violation of the API part of the API).


  **def** **fetch\_smalltable\_rows**(

      table\_handle: smalltable.Table,

      keys: Sequence\[bytes **|** str\],

      require\_all\_keys: bool **\=** False,

  ) **\-\>** Mapping\[bytes, tuple\[str, ...\]\]:

      """Fetches rows from a Smalltable.


      Retrieves rows pertaining to the given keys from the Table instance

      represented by table\_handle.  String keys will be UTF-8 encoded.


      Args:

          table\_handle: An open smalltable.Table instance.

          keys: A sequence of strings representing the key of each table

            row to fetch.  String keys will be UTF-8 encoded.

          require\_all\_keys: If True only rows with values set for all keys will be

            returned.


      Returns:

          A dict mapping keys to the corresponding table row data

          fetched. Each row is represented as a tuple of strings. For

          example:


          {b'Serak': ('Rigel VII', 'Preparer'),

           b'Zim': ('Irk', 'Invader'),

           b'Lrrr': ('Omicron Persei 8', 'Emperor')}


          Returned keys are always bytes.  If a key from the keys argument is

          missing from the dictionary, then that row was not found in the

          table (and require\_all\_keys must have been False).


      Raises:

          IOError: An error occurred accessing the smalltable.

      """


  Similarly, this variation on Args: with a line break is also allowed:


  **def** **fetch\_smalltable\_rows**(

      table\_handle: smalltable.Table,

      keys: Sequence\[bytes **|** str\],

      require\_all\_keys: bool **\=** False,

  ) **\-\>** Mapping\[bytes, tuple\[str, ...\]\]:

      """Fetches rows from a Smalltable.


      Retrieves rows pertaining to the given keys from the Table instance

      represented by table\_handle.  String keys will be UTF-8 encoded.


      Args:

        table\_handle:

          An open smalltable.Table instance.

        keys:

          A sequence of strings representing the key of each table row to

          fetch.  String keys will be UTF-8 encoded.

        require\_all\_keys:

          If True only rows with values set for all keys will be returned.


      Returns:

        A dict mapping keys to the corresponding table row data

        fetched. Each row is represented as a tuple of strings. For

        example:


        {b'Serak': ('Rigel VII', 'Preparer'),

         b'Zim': ('Irk', 'Invader'),

         b'Lrrr': ('Omicron Persei 8', 'Emperor')}


        Returned keys are always bytes.  If a key from the keys argument is

        missing from the dictionary, then that row was not found in the

        table (and require\_all\_keys must have been False).


      Raises:

        IOError: An error occurred accessing the smalltable.

      """


  4. ##### Classes

     Classes should have a docstring below the class definition describing the class. If your class has public attributes, they should be documented here in an Attributes section and follow the same formatting as a f[unction’s Args](#heading=h.gk4gqmiro98k) section.  
       
     **class** **SampleClass**:  
         """Summary of class here.  
       
         Longer class information...  
         Longer class information...  
       
         Attributes:  
             likes\_spam: A boolean indicating if we like SPAM or not.  
             eggs: An integer count of the eggs we have laid.  
         """  
       
         **def** **\_\_init\_\_**(self, likes\_spam: bool **\=** False):  
             """Initializes the instance based on spam preference.  
       
             Args:  
               likes\_spam: Defines if instance exhibits this preference.  
             """  
             self.likes\_spam **\=** likes\_spam  
             self.eggs **\=** 0  
       
         **def** **public\_method**(self):  
             """Performs operation blah."""  
       
     All class docstrings should start with a one-line summary that describes what the class instance represents. This implies that subclasses of Exception should also describe what the exception represents, and not the context in which it might occur. The class docstring should not repeat unnecessary information, such as that the class is a class.  
     

*\# Yes:*  
**class** **CheeseShopAddress**:  
  """The address of a cheese shop.

  ...  
  """

**class** **OutOfCheeseError**(Exception):  
  """No more cheese is available."""

*\# No:*  
**class** **CheeseShopAddress**:  
  """Class that describes the address of a cheese shop.

  ...  
  """

**class** **OutOfCheeseError**(Exception):  
  """Raised when no more cheese is available."""

5. ##### Block and Inline Comments

   The final place to have comments is in tricky parts of the code. If you’re going to have to explain it at the next code review, you should comment it now. Complicated operations get a few lines of comments before the operations commence. Non-obvious ones get comments at the end of the line.  
   

   *\# We use a weighted dictionary search to find out where i is in*  
   *\# the array.  We extrapolate position based on the largest num*  
   *\# in the array and the array size and then do binary search to*  
   *\# get the exact number.*  
     
   **if** i **&** (i**\-**1\) **\==** 0:  *\# True if i is 0 or a power of 2\.*

     
   To improve legibility, these comments should start at least 2 spaces away from the code with the comment character \#, followed by at least one space before the text of the comment itself.  
     
   On the other hand, never describe the code. Assume the person reading the code knows Python (though not what you’re trying to do) better than you do.  
   

   *\# BAD COMMENT: Now go through the b array and make sure whenever i occurs*  
   *\# the next element is i+1*

   

   6. ##### Punctuation, Spelling, and Grammar

      Pay attention to punctuation, spelling, and grammar; it is easier to read well-written comments than badly written ones.  
        
      Comments should be as readable as narrative text, with proper capitalization and punctuation. In many cases, complete sentences are more readable than sentence fragments. Shorter comments, such as comments at the end of a line of code, can sometimes be less formal, but you should be consistent with your style.  
        
      Although it can be frustrating to have a code reviewer point out that you are using a comma when you should be using a semicolon, it is very important that source code maintain a high level of clarity and readability. Proper punctuation, spelling, and grammar help with that goal.  
      

7. #### Strings

     
   Use an [f-string](https://docs.python.org/3/reference/lexical_analysis.html#f-strings), the  %  operator, or the  format  method for formatting strings, even when the parameters are all strings. Use your best judgment to decide between string formatting options. A single join with  \+  is okay but do not format with  \+ .  
     
   Yes: x **\=** f'name: {name}; score: {n}'  
        x **\=** '%s, %s\!' **%** (imperative, expletive)  
        x **\=** '{}, {}'.format(first, second)  
        x **\=** 'name: %s; score: %d' **%** (name, n)  
        x **\=** 'name: %(name)s; score: %(score)d' **%** {'name':name, 'score':n}  
        x **\=** 'name: {}; score: {}'.format(name, n)  
        x **\=** a **\+** b

##### 

   No: x **\=** first **\+** ', ' **\+** second

       x **\=** 'name: ' **\+** name **\+** '; score: ' **\+** str(n)

##### 

   

   Avoid using the  \+  and  \+=  operators to accumulate a string within a loop. In some conditions, accumulating a string with addition can lead to quadratic rather than linear running time. Although common accumulations of this sort may be optimized on CPython, that is an implementation detail. The conditions under which an optimization applies are not easy to predict and may change. Instead, add each substring to a list and  ''.join  the list after the loop terminates, or write each substring to an  io.StringIO  buffer. These techniques consistently have amortized-linear run-time complexity.

   

   Yes: items **\=** \['\<table\>'\]

        **for** last\_name, first\_name **in** employee\_list:

            items.append('\<tr\>\<td\>%s, %s\</td\>\</tr\>' **%** (last\_name, first\_name))

        items.append('\</table\>')

        employee\_table **\=** ''.join(items)

##### 

   No: employee\_table **\=** '\<table\>'

       **for** last\_name, first\_name **in** employee\_list:

           employee\_table **\+=** '\<tr\>\<td\>%s, %s\</td\>\</tr\>' **%** (last\_name, first\_name)

       employee\_table **\+=** '\</table\>'

##### 

   Be consistent with your choice of string quote character within a file. Pick  '  or  "  and stick with it. It is okay to use the other quote character on a string to avoid the need to backslash-escape quote characters within the string.

   Yes:

     Python('Why are you hiding your eyes?')

     Gollum("I'm scared of lint errors.")

     Narrator('"Good\!" thought a happy Python reviewer.')

##### 

##### 

   No:

     Python("Why are you hiding your eyes?")

     Gollum('The lint. It burns. It burns us.')

     Gollum("Always the great lint. Watching. Watching.")

##### 

   Prefer  """  for multi-line strings rather than  ''' . Projects may choose to use  '''  for all non-docstring multi-line strings if and only if they also use  '  for regular strings. Docstrings must use  """  regardless.

   

   Multi-line strings do not flow with the indentation of the rest of the program. If you need to avoid embedding extra space in the string, use either concatenated single-line strings or a multi-line string with  [textwrap.dedent()](https://docs.python.org/3/library/textwrap.html#textwrap.dedent)  to remove the initial space on each line:

    No:

     long\_string **\=** """This is pretty ugly.

   Don't do this.

   """

##### 

     Yes:

     long\_string **\=** """This is fine if your use case can accept

         extraneous leading spaces."""

##### 

     Yes:

     long\_string **\=** ("And this is fine if you cannot accept\\n" **\+**

                    "extraneous leading spaces.")

##### 

     Yes:

     long\_string **\=** ("And this too is fine if you cannot accept\\n"

                    "extraneous leading spaces.")

##### 

     Yes:

     **import** textwrap

   

     long\_string **\=** textwrap.dedent("""\\

         This is also fine, because textwrap.dedent()

         will collapse common leading spaces in each line.""")

##### 

   Note that using a backslash here does not violate the prohibition against [explicit line continuation](#line-length-1); in this case, the backslash is [escaping a newline](https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals) in a string literal.

   1. ##### Logging

      For logging functions that expect a pattern-string (with %-placeholders) as their first argument: Always call them with a string literal (not an f-string\!) as their first argument with pattern-parameters as subsequent arguments. Some logging implementations collect the unexpanded pattern-string as a queryable field. It also prevents spending time rendering a message that no logger is configured to output.  
      

      Yes:  
        **import** tensorflow **as** tf  
        logger **\=** tf.get\_logger()  
        logger.info('TensorFlow Version is: %s', tf.\_\_version\_\_)

        Yes:

        **import** os

        **from** absl **import** logging

      

        logging.info('Current $PAGER is: %s', os.getenv('PAGER', default**\=**''))

      

        homedir **\=** os.getenv('HOME')

        **if** homedir **is** None **or** **not** os.access(homedir, os.W\_OK):

          logging.error('Cannot write to home directory, $HOME=%r', homedir)

        No:

        **import** os

        **from** absl **import** logging

      

        logging.info('Current $PAGER is:')

        logging.info(os.getenv('PAGER', default**\=**''))

      

        homedir **\=** os.getenv('HOME')

        **if** homedir **is** None **or** **not** os.access(homedir, os.W\_OK):

          logging.error(f'Cannot write to home directory, $HOME={homedir\!r}')

      

   2. ##### Error Messages

      Error messages (such as: message strings on exceptions like ValueError, or messages shown to the user) should follow three guidelines:  
        
1. The message needs to precisely match the actual error condition.  
2. Interpolated pieces need to always be clearly identifiable as such.  
3. They should allow simple automated processing (e.g. grepping).

   Yes:

     **if** **not** 0 **\<=** p **\<=** 1:

       **raise** ValueError(f'Not a probability: {p\!r}')

   

     **try**:

       os.rmdir(workdir)

     **except** OSError **as** error:

       logging.warning('Could not remove directory (reason: %r): %r',

                       error, workdir)

   

     No:

     **if** p **\<** 0 **or** p **\>** 1:  *\# PROBLEM: also false for float('nan')\!*

       **raise** ValueError(f'Not a probability: {p\!r}')

   

     **try**:

       os.rmdir(workdir)

     **except** OSError:

       *\# PROBLEM: Message makes an assumption that might not be true:*

       *\# Deletion might have failed for some other reason, misleading*

       *\# whoever has to debug this.*

       logging.warning('Directory already was deleted: %s', workdir)

   

     **try**:

       os.rmdir(workdir)

     **except** OSError:

       *\# PROBLEM: The message is harder to grep for than necessary, and*

       *\# not universally non-confusing for all possible values of \`workdir\`.*

       *\# Imagine someone calling a library function with such code*

       *\# using a name such as workdir \= 'deleted'. The warning would read:*

       *\# "The deleted directory could not be deleted."*

       logging.warning('The %s directory could not be deleted.', workdir)

8. #### Files, Sockets, and similar Stateful Resources

     
   Explicitly close files and sockets when done with them. This rule naturally extends to closeable resources that internally use sockets, such as database connections, and also other resources that need to be closed down in a similar fashion. To name only a few examples, this also includes [mmap](https://docs.python.org/3/library/mmap.html) mappings, [h5py File objects](https://docs.h5py.org/en/stable/high/file.html), and [matplotlib.pyplot figure windows](https://matplotlib.org/2.1.0/api/_as_gen/matplotlib.pyplot.close.html).  
     
   Leaving files, sockets or other such stateful objects open unnecessarily has many downsides:  
     
* They may consume limited system resources, such as file descriptors. Code that deals with many such objects may exhaust those resources unnecessarily if they’re not returned to the system promptly after use.  
* Holding files open may prevent other actions such as moving or deleting them, or unmounting a filesystem.  
* Files and sockets that are shared throughout a program may inadvertently be read from or written to after logically being closed. If they are actually closed, attempts to read or write from them will raise exceptions, making the problem known sooner.  
    
  Furthermore, while files and sockets (and some similarly behaving resources) are automatically closed when the object is destructed, coupling the lifetime of the object to the state of the resource is poor practice:  
    
* There are no guarantees as to when the runtime will actually invoke the \_\_del\_\_ method. Different Python implementations use different memory management techniques, such as delayed garbage collection, which may increase the object’s lifetime arbitrarily and indefinitely.  
* Unexpected references to the file, e.g. in globals or exception tracebacks, may keep it around longer than intended.  
    
  Relying on finalizers to do automatic cleanup that has observable side effects has been rediscovered over and over again to lead to major problems, across many decades and multiple languages.  
    
  The preferred way to manage files and similar resources is using the  [with  statement](https://docs.python.org/3/reference/compound_stmts.html#the-with-statement):  
    
  **with** open("hello.txt") **as** hello\_file:  
      **for** line **in** hello\_file:  
          **print**(line)  
    
  For file-like objects that do not support the with statement, use  contextlib.closing() :  
    
  **import** contextlib  
    
  **with** contextlib.closing(urllib.urlopen("http://www.python.org/")) **as** front\_page:  
      **for** line **in** front\_page:  
          **print**(line)  
    
  In rare cases where context-based resource management is infeasible, code documentation must explain clearly how resource lifetime is managed.

9. #### TODO Comments

   Use  TODO  comments for code that is temporary, a short-term solution, or good-enough but not perfect.  
     
     
   A  TODO  comment begins with the word  TODO  in all caps, a following colon, and a link to a resource that contains the context, ideally a bug reference. A bug reference is preferable because bugs are tracked and have follow-up comments. Follow this piece of context with an explanatory string introduced with a hyphen  \- . The purpose is to have a consistent  TODO  format that can be searched to find out how to get more details.  
     
   *\# TODO: crbug.com/192795 \- Investigate cpufreq optimizations.*  
     
   Old style, formerly recommended, but discouraged for use in new code:  
     
   *\# TODO(crbug.com/192795): Investigate cpufreq optimizations.*  
   *\# TODO(yourusername): Use a "\\\*" here for concatenation operator.*  
     
   Avoid adding TODOs that refer to an individual or team as the context:  
     
   *\# TODO: @yourusername \- File an issue and use a '\*' for repetition.*  
     
   If your  TODO  is of the form “At a future date do something” make sure that you either include a very specific date (“Fix by November 2009”) or a very specific event (“Remove this code when all clients can handle XML responses.”) that future code maintainers will comprehend. Issues are ideal for tracking this.  
   

10. #### Imports formatting

      
    Imports should be on separate lines; there are [exceptions for  typing  and  collections.abc  imports](#imports-for-typing).  
      
    E.g.:

    Yes: **from** collections.abc **import** Mapping, Sequence

         **import** os

         **import** sys

         **from** typing **import** Any, NewType

    No:  **import** os, sys

    Imports are always put at the top of the file, just after any module comments and docstrings and before module globals and constants. Imports should be grouped from most generic to least generic:

    

1. Python future import statements. For example:

   

   **from** \_\_future\_\_ **import** annotations

   

   See above for more information about those.

   

2. Python standard library imports. For example:

   

   **import** sys

   

3. third-party module or package imports. For example:

   

   **import** tensorflow **as** tf

   

4. Code repository sub-package imports. For example:

   

   **from** otherproject.ai **import** mind

5. **Deprecated**: application-specific imports that are part of the same top-level sub-package as this file. For example:

   

   **from** myproject.backend.hgwells **import** time\_machine

   You may find older Google Python Style code doing this, but it is no longer required. New code is encouraged not to bother with this. Simply treat application-specific sub-package imports the same as other sub-package imports.

   

   Within each grouping, imports should be sorted lexicographically, ignoring case, according to each module’s full package path (the path in from path import ...). Code may optionally place a blank line between import sections.

   

   **import** collections

   **import** queue

   **import** sys

   

   **from** absl **import** app

   **from** absl **import** flags

   **import** bs4

   **import** cryptography

   **import** tensorflow **as** tf

   

   **from** book.genres **import** scifi

   **from** myproject.backend **import** huxley

   **from** myproject.backend.hgwells **import** time\_machine

   **from** myproject.backend.state\_machine **import** main\_loop

   **from** otherproject.ai **import** body

   **from** otherproject.ai **import** mind

   **from** otherproject.ai **import** soul

   

   *\# Older style code may have these imports down here instead:*

   *\#from myproject.backend.hgwells import time\_machine*

   *\#from myproject.backend.state\_machine import main\_loop*

11. #### Statements

      
    Generally only one statement per line.  
      
    However, you may put the result of a test on the same line as the test only if the entire statement fits on one line. In particular, you can never do so with try/except since the try and except can’t both fit on the same line, and you can only do so with an if if there is no else.

    Yes:

    

      **if** foo: bar(foo)

    No:

    

      **if** foo: bar(foo)

      **else**:   baz(foo)

    

      **try**:               bar(foo)

      **except** ValueError: baz(foo)

    

      **try**:

          bar(foo)

      **except** ValueError: baz(foo)

12. #### Getters and Setters

      
    Getter and setter functions (also called accessors and mutators) should be used when they provide a meaningful role or behavior for getting or setting a variable’s value.  
      
    In particular, they should be used when getting or setting the variable is complex or the cost is significant, either currently or in a reasonable future.  
      
    If, for example, a pair of getters/setters simply read and write an internal attribute, the internal attribute should be made public instead. By comparison, if setting a variable means some state is invalidated or rebuilt, it should be a setter function. The function invocation hints that a potentially non-trivial operation is occurring. Alternatively, [properties](#properties) may be an option when simple logic is needed, or refactoring to no longer need getters and setters.  
      
    Getters and setters should follow the [Naming](#naming) guidelines, such as  get\_foo()  and  set\_foo().  
      
    If the past behavior allowed access through a property, do not bind the new getter/setter functions to the property. Any code still attempting to access the variable by the old method should break visibly so they are made aware of the change in complexity.  
    

13. #### Naming {#naming}

      
    module\_name, package\_name, ClassName, method\_name, ExceptionName, function\_name, GLOBAL\_CONSTANT\_NAME, global\_var\_name, instance\_var\_name, function\_parameter\_name, local\_var\_name, query\_proper\_noun\_for\_thing, send\_acronym\_via\_https.  
      
    Function names, variable names, and filenames should be descriptive; avoid abbreviation. In particular, do not use abbreviations that are ambiguous or unfamiliar to readers outside your project, and do not abbreviate by deleting letters within a word.  
      
    Always use a  .py  filename extension. Never use dashes.

    1. ##### Names to Avoid

* single character names, except for specifically allowed cases:


  * counters or iterators (e.g. i, j, k, v, et al.)  
  * e as an exception identifier in try/except statements.  
  * f as a file handle in with statements  
  * private type variables with no constraints (e.g. \_T \= TypeVar("\_T"), \_P \= ParamSpec("\_P"))

    

    Please be mindful not to abuse single-character naming. Generally speaking, descriptiveness should be proportional to the name’s scope of visibility. For example, i might be a fine name for 5-line code block but within multiple nested scopes, it is likely too vague.

    

* dashes (-) in any package/module name


* \_\_double\_leading\_and\_trailing\_underscore\_\_ names (reserved by Python)


* offensive terms


* names that needlessly include the type of the variable (for example:  id\_to\_name\_dict )

  2. ##### Naming Conventions

* “Internal” means internal to a module, or protected or private within a class.


* Prepending a single underscore (\_) has some support for protecting module variables and functions (linters will flag protected member access). Note that it is okay for unit tests to access protected constants from the modules under test.


* Prepending a double underscore (\_\_ aka “dunder”) to an instance variable or method effectively makes the variable or method private to its class (using name mangling); we discourage its use as it impacts readability and testability, and isn’t really private. Prefer a single underscore.


* Place related classes and top-level functions together in a module. Unlike Java, there is no need to limit yourself to one class per module.


* Use CapWords for class names, but lower\_with\_under.py for module names. Although there are some old modules named CapWords.py, this is now discouraged because it’s confusing when the module happens to be named after a class. (“wait – did I write import StringIO or from StringIO import StringIO?”)


* New unit test files follow PEP 8 compliant lower\_with\_under method names, for example, test\_\<method\_under\_test\>\_\<state\>. For consistency(\*) with legacy modules that follow CapWords function names, underscores may appear in method names starting with test to separate logical components of the name. One possible pattern is test\<MethodUnderTest\>\_\<state\>.


  3. ##### File Naming

     Python filenames must have a .py extension and must not contain dashes (-). This allows them to be imported and unittested. If you want an executable to be accessible without the extension, use a symbolic link or a simple bash wrapper containing exec "$0.py" "$@".

  4. ##### Guidelines derived from Guido’s Recommendations

| Type | Public | Internal |
| :---- | :---- | :---- |
| Packages | lower\_with\_under |  |
| Modules | lower\_with\_under | \_lower\_with\_under |
| Classes | CapWords | \_CapWords |
| Exceptions | CapWords |  |
| Functions | lower\_with\_under() | \_lower\_with\_under() |
| Global/Class Constants | CAPS\_WITH\_UNDER | \_CAPS\_WITH\_UNDER |
| Global/Class Variables | lower\_with\_under | \_lower\_with\_under |
| Instance Variables | lower\_with\_under | \_lower\_with\_under (protected) |
| Method Names | lower\_with\_under() | \_lower\_with\_under() (protected) |
| Function/Method Parameters | lower\_with\_under |  |
| Local Variables | lower\_with\_under  |  |

  5. ##### Mathematical Notation

     For mathematically heavy code, short variable names that would otherwise violate the style guide are preferred when they match established notation in a reference paper or algorithm. When doing so, reference the source of all naming conventions in a comment or docstring or, if the source is not accessible, clearly document the naming conventions. Prefer PEP8-compliant descriptive\_names for public APIs, which are much more likely to be encountered out of context.


14. #### Main

      
    In Python, pydoc as well as unit tests require modules to be importable. If a file is meant to be used as an executable, its main functionality should be in a main() function, and your code should always check if \_\_name\_\_ \== '\_\_main\_\_' before executing your main program, so that it is not executed when the module is imported.  
      
    When using absl, use app.run:  
      
    **from** absl **import** app  
    ...  
      
    **def** **main**(argv: Sequence\[str\]):  
        *\# process non-flag arguments*  
        ...  
      
    **if** \_\_name\_\_ **\==** '\_\_main\_\_':  
        app.run(main)  
      
    Otherwise, use:  
      
    **def** **main**():  
        ...  
      
    **if** \_\_name\_\_ **\==** '\_\_main\_\_':  
        main()  
      
    All code at the top level will be executed when the module is imported. Be careful not to call functions, create objects, or perform other operations that should not be executed when the file is being  pydoc ed.

15. #### Function length

    Prefer small and focused functions.  
      
    We recognize that long functions are sometimes appropriate, so no hard limit is placed on function length. If a function exceeds about 40 lines, think about whether it can be broken up without harming the structure of the program.  
      
    Even if your long function works perfectly now, someone modifying it in a few months may add new behavior. This could result in bugs that are hard to find. Keeping your functions short and simple makes it easier for other people to read and modify your code.  
      
      
      
    You could find long and complicated functions when working with some code. Do not be intimidated by modifying existing code: if working with such a function proves to be difficult, you   
      
    find that errors are hard to debug, or you want to use a piece of it in several different contexts, consider breaking up the function into smaller and more manageable pieces.  
    

16. #### Type Annotations

    

    1. ##### General Rules

* Familiarize yourself with PEP-484.


* In methods, only annotate self, or cls if it is necessary for proper type information. e.g.,


  **@**classmethod

  **def** **create**(cls: Type\[\_T\]) **\-\>** \_T:

    **return** cls()


* Similarly, don’t feel compelled to annotate the return value of \_\_init\_\_ (where None is the only valid option).


* If any other variable or a returned type should not be expressed, use Any.


* You are not required to annotate all the functions in a module.


  * At least annotate your public APIs.  
  * Use judgment to get to a good balance between safety and clarity on the one hand, and flexibility on the other.  
  * Annotate code that is prone to type-related errors (previous bugs or complexity).  
  * Annotate code that is hard to understand.  
  * Annotate code as it becomes stable from a types perspective. In many cases, you can annotate all the functions in mature code without losing too much flexibility.

    

  2. ##### Line Breaking

     Try to follow the existing [indentation](#indentation-1) rules.  
       
     After annotating, many function signatures will become “one parameter per line”. To ensure the return type is also given its own line, a comma can be placed after the last parameter.  
       
     **def** **my\_method**(  
         self,  
         first\_var: int,  
         second\_var: Foo,  
         third\_var: Bar **|** None,  
     ) **\-\>** int:  
       ...  
       
     Always prefer breaking between variables, and not, for example, between variable names and type annotations. However, if everything fits on the same line, go for it.  
       
     **def** **my\_method**(self, first\_var: int) **\-\>** int:  
       ...  
       
     If the combination of the function name, the last parameter, and the return type is too long, indent by 4 in a new line. When using line breaks, prefer putting each parameter and the return type on their own lines and aligning the closing parenthesis with the def:  
       
     Yes:  
     **def** **my\_method**(  
         self,  
         other\_arg: MyLongType **|** None,  
     ) **\-\>** tuple\[MyLongType1, MyLongType1\]:  
       ...  
     Optionally, the return type may be put on the same line as the last parameter:  
       
     Okay:  
     **def** **my\_method**(  
         self,  
         first\_var: int,  
         second\_var: int) **\-\>** dict\[OtherLongType, MyLongType\]:  
       ...  
       
     pylint allows you to move the closing parenthesis to a new line and align with the opening one, but this is less readable.  
       
     No:  
     **def** **my\_method**(self,  
                   other\_arg: MyLongType **|** None,  
                  ) **\-\>** dict\[OtherLongType, MyLongType\]:  
       ...  
       
     As in the examples above, prefer not to break types. However, sometimes they are too long to be on a single line (try to keep sub-types unbroken).  
       
     **def** **my\_method**(  
         self,  
         first\_var: tuple\[list\[MyLongType1\],  
                          list\[MyLongType2\]\],  
         second\_var: list\[dict\[  
             MyLongType3, MyLongType4\]\],  
     ) **\-\>** None:  
       ...  
       
     If a single name and type is too long, consider using an [alias](#type-aliases) for the type. The last resort is to break after the colon and indent by 4\.

     Yes:

     **def** **my\_function**(

         long\_variable\_name:

             long\_module\_name.LongTypeName,

     ) **\-\>** None:

       ...

     No:

     **def** **my\_function**(

         long\_variable\_name: long\_module\_name.

             LongTypeName,

     ) **\-\>** None:

       ...

  3. ##### Forward Declarations

     If you need to use a class name (from the same module) that is not yet defined – for example, if you need the class name inside the declaration of that class, or if you use a class that is defined later in the code – either use from \_\_future\_\_ import annotations or use a string for the class name.

     Yes:

     **from** \_\_future\_\_ **import** annotations

     

     **class** **MyClass**:

       **def** **\_\_init\_\_**(self, stack: Sequence\[MyClass\], item: OtherClass) **\-\>** None:

     

     **class** **OtherClass**:

       ...

     Yes:

     **class** **MyClass**:

       **def** **\_\_init\_\_**(self, stack: Sequence\['MyClass'\], item: 'OtherClass') **\-\>** None:

     

     **class** **OtherClass**:

       ...

  4. ##### Default Values

     As per [PEP-008](https://peps.python.org/pep-0008/#other-recommendations), use spaces around the \= only for arguments that have both a type annotation and a default value.

     Yes:

     **def** **func**(a: int **\=** 0) **\-\>** int:

       ...

     No:

     **def** **func**(a:int**\=**0) **\-\>** int:

       ...

  5. ##### NoneType

     In the Python type system, NoneType is a “first-class” type, and for typing purposes, None is an alias for NoneType. If an argument can be None, it has to be declared\! You can use | union type expressions (recommended in new Python 3.10+ code), or the older Optional and Union syntaxes.  
       
     Use explicit X | None instead of implicit. Earlier versions of PEP 484 allowed a: str \= None to be interpreted as a: str | None \= None, but that is no longer the preferred behavior.

     Yes:

     **def** **modern\_or\_union**(a: str **|** int **|** None, b: str **|** None **\=** None) **\-\>** str:

       ...

     **def** **union\_optional**(a: Union\[str, int, None\], b: Optional\[str\] **\=** None) **\-\>** str:

       ...

     No:

     **def** **nullable\_union**(a: Union\[None, str\]) **\-\>** str:

       ...

     **def** **implicit\_optional**(a: str **\=** None) **\-\>** str:

       `...`

  6. ##### Type Aliases {#type-aliases}

     You can declare aliases of complex types. The name of an alias should be CapWorded. If the alias is used only in this module, it should be \_Private.  
       
     Note that the: TypeAlias annotation is only supported in versions 3.10+.  
       
     **from** typing **import** TypeAlias  
       
     \_LossAndGradient: TypeAlias **\=** tuple\[tf.Tensor, tf.Tensor\]  
     ComplexTFMap: TypeAlias **\=** Mapping\[str, \_LossAndGradient\]

  7. ##### Ignoring Types

     You can disable type-checking on a line with the special comment \# type: ignore.  
       
     pytype has a disable option for specific errors (similar to lint):  
       
     *\# pytype: disable=attribute-error*

  8. ##### Typing Variables

     ###### *Annotated Assignments*

     If an internal variable has a type that is hard or impossible to infer, specify its type with an annotated assignment \- use a colon and type between the variable name and value (the same as is done with function arguments that have a default value):

     

  a: Foo **\=** SomeUndecoratedFunction()

     ###### *Type Comments*

			  
Though you may see them remaining in the codebase (they were necessary before Python 3.6), do not add any more uses of a \# type: \<type name\> comment at the end of the line:

a **\=** SomeUndecoratedFunction()  *\# type: Foo*

9. ##### Tuples vs Lists

   Typed lists can only contain objects of a single type. Typed tuples can either have a single repeated type or a set number of elements with different types. The latter is commonly used as the return type from a function.  
   

   a: list\[int\] **\=** \[1, 2, 3\]  
   b: tuple\[int, ...\] **\=** (1, 2, 3)  
   c: tuple\[int, str, float\] **\=** (1, "2", 3.5)

   10. ##### Type Variables {#type-variables}

       The Python type system has [generics](https://peps.python.org/pep-0484/#generics). A type variable, such as TypeVar and ParamSpec, is a common way to use them.  
         
       Example:  
       

   **from** collections.abc **import** Callable  
   **from** typing **import** ParamSpec, TypeVar  
   \_P **\=** ParamSpec("\_P")  
   \_T **\=** TypeVar("\_T")  
   ...  
   **def** **next**(l: list\[\_T\]) **\-\>** \_T:  
     **return** l.pop()  
     
   **def** **print\_when\_called**(f: Callable\[\_P, \_T\]) **\-\>** Callable\[\_P, \_T\]:  
     **def** **inner**(**\***args: \_P.args, **\*\***kwargs: \_P.kwargs) **\-\>** \_T:  
       **print**("Function was called")  
       **return** f(**\***args, **\*\***kwargs)  
     **return** inner

         
       A TypeVar can be constrained:  
       

   AddableType **\=** TypeVar("AddableType", int, float, str)  
   **def** **add**(a: AddableType, b: AddableType) **\-\>** AddableType:  
     **return** a **\+** b

         
       A common predefined type variable in the typing module is AnyStr. Use it for multiple annotations that can be bytes or str and must all be the same type.  
       

   **from** typing **import** AnyStr  
   **def** **check\_length**(x: AnyStr) **\-\>** AnyStr:  
     **if** len(x) **\<=** 42:  
       **return** x  
     **raise** ValueError()

         
       A type variable must have a descriptive name unless it meets all of the following criteria:  
         
* not externally visible  
* not constrained  
  Yes:  
    \_T **\=** TypeVar("\_T")  
    \_P **\=** ParamSpec("\_P")  
    AddableType **\=** TypeVar("AddableType", int, float, str)  
    AnyFunction **\=** TypeVar("AnyFunction", bound**\=**Callable)

  No:

    T **\=** TypeVar("T")

    P **\=** ParamSpec("P")

    \_T **\=** TypeVar("\_T", int, float, str)

    \_F **\=** TypeVar("\_F", bound**\=**Callable)

  11. ##### String types

      Do not use typing. Text in new code. It’s only for Python 2/3 compatibility.  
        
      Use str for string/text data. For code that deals with binary data, use bytes.  
      

  **def** **deals\_with\_text\_data**(x: str) **\-\>** str:  
    ...  
  **def** **deals\_with\_binary\_data**(x: bytes) **\-\>** bytes:  
    ...

        
      If all the string types of a function are always the same, for example, if the return type is the same as the argument type in the code above, use [AnyStr](#type-variables).

  12. ##### Imports For Typing {#imports-for-typing}

      For symbols (including types, functions, and constants) from the typing or collections.abc modules used to support static analysis and type checking, always import the symbol itself. This keeps common annotations more concise and matches typing practices used worldwide. You are explicitly allowed to import multiple specific symbols on one line from the typing and collections.abc modules. For example:

  **from** collections.abc **import** Mapping, Sequence  
  **from** typing **import** Any, Generic, cast, TYPE\_CHECKING

      Given that this way of importing adds items to the local namespace, names in typing or collections. abc should be treated similarly to keywords, and not be defined in your Python code, typed or not. If there is a collision between a type and an existing name in a module, import it using import x as y.  
      

  **from** typing **import** Any **as** AnyType

        
      Prefer to use built-in types as annotations where available. Python supports type annotations using parametric container types via [PEP-585](https://peps.python.org/pep-0585/), introduced in Python 3.9.  
      

  **def** **generate\_foo\_scores**(foo: set\[str\]) **\-\>** list\[float\]:  
    ...

  13. ##### Conditional Imports

      Use conditional imports only in exceptional cases where the additional imports needed for type checking must be avoided at runtime. This pattern is discouraged; alternatives such as refactoring the code to allow top-level imports should be preferred.  
        
      Imports needed only for type annotations can be placed within an if TYPE\_CHECKING: block.  
        
* Conditionally imported types need to be referenced as strings, to be forward compatible with Python 3.6 where the annotation expressions are actually evaluated.  
* Only entities that are used solely for typing should be defined here; this includes aliases. Otherwise, it will be a runtime error, as the module will not be imported at runtime.  
* The block should be right after all the normal imports.  
* There should be no empty lines in the typing imports list.  
* Sort this list as if it were a regular import list.


  **import** typing

  **if** typing.TYPE\_CHECKING:

    **import** sketch

  **def** **f**(x: "sketch.Sketch"): ...

  14. ##### Circular Dependencies

      Circular dependencies that are caused by typing are code smells. Such code is a good candidate for refactoring. Although technically it is possible to keep circular dependencies, various build systems will not let you do so because each module has to depend on the other.  
        
      Replace modules that create circular dependency imports with Any. Set an alias with a meaningful name, and use the real type name from this module (any attribute of Any is Any). Alias definitions should be separated from the last import by one line.  
      

  **from** typing **import** Any  
    
  some\_mod **\=** Any  *\# some\_mod.py imports this module.*  
  ...  
    
  **def** **my\_method**(self, var: "some\_mod.SomeType") **\-\>** None:  
    `...`

##### 

  15. ##### Generics

      When annotating, prefer to specify type parameters for generic types; otherwise, [the generics’ parameters will be assumed to be  Any](https://peps.python.org/pep-0484/#the-any-type) .

  *\# Yes:*

  **def** **get\_names**(employee\_ids: Sequence\[int\]) **\-\>** Mapping\[int, str\]:

    ...

  *\# No:*

  *\# This is interpreted as get\_names(employee\_ids: Sequence\[Any\]) \-\> Mapping\[Any, Any\]*

  **def** **get\_names**(employee\_ids: Sequence) **\-\>** Mapping:

    ...

      If the best type parameter for a generic is Any, make it explicit, but remember that in many cases [TypeVar](#type-variables) might be more appropriate:

  *\# No:*

  **def** **get\_names**(employee\_ids: Sequence\[Any\]) **\-\>** Mapping\[Any, str\]:

    """Returns a mapping from employee ID to employee name for given IDs."""

  *\# Yes:*

  \_T **\=** TypeVar('\_T')

  **def** **get\_names**(employee\_ids: Sequence\[\_T\]) **\-\>** Mapping\[\_T, str\]:

    """Returns a mapping from employee ID to employee name for given IDs."""

      

# Performance Considerations {#performance-considerations}

### **Techniques for optimizing Python code** {#techniques-for-optimizing-python-code}

Python developers need to be able to use code optimization techniques instead of basic programming to ensure applications run smoothly and quickly.

1. ####  Apply the Peephole Optimization Technique

     
   \<Peephole\> is a code optimization technique in Python that is done at compile time to improve your code performance. With the Peephole optimization technique, code is optimized behind the scenes and is done either by pre-calculating constant expressions or by using membership tests.  
     
   Using this technique, developers can replace a section of the program or a segment of instruction without significant changes in output. 

   def peephole\_func():

   	a \= "Hello, world\!" \* 5

   	b \= \[1,2 \] \* 7

   	c \= (10, 20, 30) \* 3

   	print(a, b, c)

   peephole\_func.\_\_code\_\_.co\_consts: (

		None  
		Hello, world\!Hello, world\!Hello, world\!Hello, world\!Hello, world\!  
		1  
		2  
		7  
		(10, 20, 30, 10, 20, 30, 10, 20, 30)  
	)

	peephole\_func.\_\_code\_\_.co\_varnames: ('a', 'b', 'c')

	peephole\_func.\_\_code\_\_.co\_names: ('print',)

###### 

2. ####  Intern Strings for Efficiency

     
   When augmenting strings with characters of varying sizes, the overall size increases beyond the added character's dimensions due to extra information allocated by Python for string storage. To address this, employ the optimization technique of string interning, caching specific strings in memory upon creation to have only one active instance at any time, thereby minimizing additional memory requirements.   
   Prioritize identifier strings, such as attribute and variable names, for internment, and adhere to principles governing when to intern strings, considering factors like compile-time constants, string length, and naming conventions.  
     
   When handling external strings, be mindful that those from files or networks are not automatically interned, necessitating the use of the **intern()** function for optimized performance.

3. ####  Code profiling

   Two primary methods for profiling include using   
* \<timeit\>   
* \<cProfile\>


  \<timeit\> serves as a stopwatch profiler, recording the execution time of a code segment in milliseconds. On the other hand, \<cProfile\> offers advanced profiling integrated into the Python package since Python 2.5. It can be applied by wrapping a function inside its run method or by running the entire script with cProfile activated as a command line argument using Python's "-m" option. 


  Analyzing the key elements of a \<cProfile\> report, such as \<ncalls\>, \<tottime\>, \<percall\>, \<cumtime\>, and \<filename\_lineno(function)\>, allows you to pinpoint bottlenecks in your code.

4. ####  Use Generators and Keys For Sorting

   Optimizing memory usage can be achieved efficiently through the strategic use of generators. Generators exhibit the unique characteristic of not returning all items at once, but rather, they yield one item at a time, significantly reducing the memory footprint. When sorting items in a list, it is recommended to utilize keys and the default **sort()** method. This approach allows for sorting lists and strings based on a specified index provided as part of the key argument, providing a more streamlined and memory-conscious sorting process.

5. #### Built-in Operators and External Libraries

   Utilizing built-ins enhances code efficiency as they are pre-compiled, ensuring swift execution. Additionally, exploring the "C" equivalents of Python libraries, such as using cPickle instead of Pickle, can significantly boost performance. This optimization extends further with tools like PyPy and Cython, offering a pathway to enhance speed through static compilation. 

6. #### Avoid Using Globals

   Globals can have non-obvious and hidden side effects resulting in Spaghetti code. Python is slow at accessing external variables. Herewith, it’s better to avoid using them, or at least limit their usage. If they are a necessity, here are a few recommendations:

* Use the global keyword to declare an external variable  
* Make a local copy before using them inside loops.  
    
  


7. ####  Limiting Method Lookup

   To optimize method lookup in Python, developers can store a reference to a method or function in a local variable rather than repeatedly accessing it through attribute lookup. This can be particularly useful in loops or frequently called functions.

   \# Non-optimized code

   for item in my\_list:

       result \= some\_object.some\_method(item)

   

   \# Optimized code

   some\_method \= some\_object.some\_method  \# Store a reference

   for item in my\_list:

       result \= some\_method(item)  \# Use the local reference

   

   By doing this, you reduce the overhead of attribute lookup on each iteration, potentially improving performance.

8. #### Optimizing with String Operations

   String concatenation can be slow, especially when performed in a loop. In such cases, using a list to accumulate parts of the string and then joining them at the end can be much more efficient. 

   \# Non-optimized code

   result \= ""

   for item in my\_list:

       result \+= str(item)

   

   \# Optimized code

   result\_parts \= \[\]

   for item in my\_list:

       result\_parts.append(str(item))

   result \= "".join(result\_parts)

   The optimized code avoids creating unnecessary intermediate string objects during concatenation.

9. #### Optimizing with if Statements

   Minimizing the number of if statements or optimizing their structure can also improve code performance. Use early returns when possible to avoid unnecessary condition checking.

   \# Non-optimized code

   def process\_data(data):

       if data:

           \# Perform some operation

       else:

           \# Handle the empty data case

   

   \# Optimized code

   def process\_data(data):

       if not data:

           \# Handle the empty data case

           return

       

       \# Perform some operation

   

   In the optimized code, the function avoids the need to check the data condition twice and simplifies the code flow.

# Security Considerations {#security-considerations}

Ensuring robust security measures is paramount in Python development. Adhering to our Python Coding Guidelines, this section outlines key considerations and best practices to fortify the security of Python code.

1. ### **Input Validation and Sanitization:** {#input-validation-and-sanitization:}

   Implement thorough input validation to prevent injection attacks.  
   Sanitize user inputs to mitigate the risk of malicious data manipulation.

2. ### **Avoiding Hardcoded Credentials:** {#avoiding-hardcoded-credentials:}

   Refrain from hardcoding sensitive information such as passwords and API keys.  
   Utilize secure storage solutions or environment variables for managing credentials.

3. ### **Secure File Handling:** {#secure-file-handling:}

   Validate file types and extensions to prevent arbitrary file execution.  
   Implement proper file permissions to restrict unauthorized access.

4. ### **SSL/TLS Usage:** {#ssl/tls-usage:}

   Ensure secure communication by using SSL/TLS for network interactions.  
   Verify the validity of SSL certificates to prevent man-in-the-middle attacks.

5. ### **Dependency Scanning:** {#dependency-scanning:}

   Regularly scan and update dependencies to address security vulnerabilities.  
   Utilize tools like safety or bandit to automate the identification of insecure dependencies.

6. ### **Code Review for Security:** {#code-review-for-security:}

   Conduct regular code reviews with a focus on security.  
   Identify and remediate potential vulnerabilities through thorough peer assessments.

7. ### **Cross-Site Scripting (XSS) and Cross-Site Request Forgery (CSRF) Mitigation:** {#cross-site-scripting-(xss)-and-cross-site-request-forgery-(csrf)-mitigation:}

   Implement secure coding practices to prevent XSS and CSRF attacks.  
   Utilize frameworks' built-in features for additional protection.

8. ### **Authentication and Authorization:** {#authentication-and-authorization:}

   Employ strong authentication mechanisms and enforce least privilege principles.  
   Regularly audit and update access controls to reflect changes in the application's requirements.

9. ### **Logging and Monitoring:** {#logging-and-monitoring:}

   Implement logging for security-relevant events to facilitate post-incident analysis.  
   Establish monitoring systems to detect and respond to potential security breaches.

10. ### **Data Encryption:** {#data-encryption:}

    Encrypt sensitive data at rest and in transit.  
    Use strong encryption algorithms and adhere to industry best practices.

# Portability {#portability}

Achieving portability in Python code is crucial for enabling seamless execution across diverse platforms. 

1. ### **Version Compatibility:**

   Validate compatibility with different Python versions to accommodate users on varying releases.Clearly specify the minimum Python version required for the code to run successfully.

2. ### **Dependency Management:**

   Utilize virtual environments to isolate dependencies and avoid conflicts between project requirements.Document and manage dependencies explicitly, ensuring compatibility with the target platforms.

3. ### **Cross-Platform Testing:**

   Regularly conduct tests on multiple operating systems to identify and address platform-specific issues.Employ continuous integration tools to automate cross-platform testing and ensure ongoing compatibility.

4. ### **File System Considerations:**

   Use platform-independent file paths and avoid hardcoding directory structures specific to a single operating system.Be mindful of case sensitivity differences in file paths when working across Windows, macOS, and Linux.

5. ### **Standard Libraries and Built-ins:**

   Rely on Python's standard libraries and built-in modules to maximize portability.  
   Verify the availability and consistency of standard functionality across different Python implementations.

6. ### **Avoiding Platform-Specific Features:**

   Refrain from using features specific to a particular platform unless necessary.When platform-specific functionality is unavoidable, provide conditional checks to handle variations.

7. ### **Executable Scripts:**

   Use platform-independent shebangs (e.g., \#\!/usr/bin/env python) in executable scripts.  
   Consider using tools like PyInstaller or cx\_Freeze for packaging scripts into standalone executables for different platforms.

8. ### **GUI Framework Considerations:**

   If developing graphical user interfaces (GUIs), choose cross-platform GUI frameworks like Tkinter or PyQt that offer consistent behavior across operating systems.Address platform-specific styling and behavior nuances to ensure a uniform user experience.

9. ### **Documentation for Platform-Specific Configurations:**

   Clearly document any platform-specific configurations or considerations in the project documentation.Provide guidance for users on adapting the code to different platforms if necessary.

# Version Control {#version-control-1}

Effective version control is paramount in Python development to manage code changes, collaborate seamlessly, and ensure project integrity. 

1. ### **Use Meaningful Commit Messages:**

   Craft clear, concise, and descriptive commit messages that convey the purpose of the change.Follow a consistent message format to facilitate easy tracking and comprehension.

2. ### **Frequent Commits with Atomic Changes:**

   Commit changes in small, logical units, focusing on a single task or feature.  
   Make frequent, atomic commits to create a granular and comprehensible version history.

3. ### **Branching Strategy:**

   Adopt a branching strategy (e.g., Gitflow) that suits the project's needs.  
   Utilize feature branches for new functionalities and hotfix branches for addressing critical issues.

4. ### **Pull Requests and Code Reviews:**

   Open pull requests for feature additions or bug fixes.  
   Conduct thorough code reviews to ensure code quality, adherence to coding standards, and knowledge sharing among team members.

5. ### **.gitignore File:**

   Configure a comprehensive .gitignore file to exclude unnecessary files and directories (e.g., virtual environments, compiled binaries) from version control.

6. ### **Semantic Versioning:**

   Adhere to semantic versioning principles (MAJOR.MINOR.PATCH) to convey the nature of changes in releases. Use tags to mark significant points in the project's development history.

7. ### **Rebase Instead of Merge:**

   Consider rebasing instead of merging for a cleaner version history.  
   Resolve conflicts promptly to maintain a smooth and linear project history.

8. ### **Version Control Hooks:**

   Implement pre-commit hooks to enforce code formatting, linting, and other checks.  
   Utilize server-side hooks to integrate automated testing before accepting changes.

9. ### **Continuous Integration (CI):**

   Integrate Git with a CI/CD pipeline to automate testing and deployment processes.  
   Ensure that the CI pipeline runs on feature branches and pull requests.

10. ### **Documentation in Repository:**

    Maintain a comprehensive README.md file with instructions for setting up the development environment, running tests, and contributing to the project.  
    Document any project-specific version control practices.

11. ### **Secure Credentials Handling:**

    Avoid committing sensitive information, such as API keys or credentials, to the repository.  
    Utilize environment variables or configuration files for managing sensitive data.

[image1]: <data:image/png;base64,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>
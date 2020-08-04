# Aplazame backend


![test](https://github.com/kingoodie/aplazame-backend/workflows/test/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/kingoodie/aplazame-backend/branch/master/graph/badge.svg?token=T6GDCHEMI3)](https://codecov.io/gh/kingoodie/aplazame-backend)
[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/5143f4e5a1bde13da691)

It would remain to do the tests on the business endpoints.

## Install

    pip install poetry
    poetry install

    
## Run

Firstly, rename the file `sample.env` to `.env` and fill with values if needed.

To run the server execute:

    poetry run uvicorn api.app:app --port 80 --env-file .env
    

## Test

    poetry run pytest

## Docker

To run with docker execute:

    docker-compose build
    docker-compose up
    
## Deploy

The project deploys itself to the instance each time a commit is made through Github Actions.

## Objetivos a completar

1) Indica cómo se puede optimizar el rendimiento del servicio de listado de operaciones.

    ```
    Para acelerar la consulta del listado de operaciones tenemos que decirle
    al ORM en cuestión que en las consultas a las cuentas de cliente o comercios
    se traiga a la misma vez las operaciones o transacciones de cada una de las cuentas. Esto
    se haría con el ORM de Django con prefetch_related (igual en Tortoise ORM),
    ya que la relación entre las cuentas y las transacciones es de 1 a muchos. Si
    no hicieramos esto, por cada relacion entre cuenta y transacción habría que
    hacer una consulta adicional si quisieramos obtener los datos de la transacciones.
   
    Aparte de esto, podríamos cachear la respuesta, así nos "ahorraríamos" el coste de 
    las subsiguientes consultas a los mismas cuentas, si no hubiera actualización. El problema sería que habría
    que crear otro mecanismo adicional de invalidación de caché.
   
    Creo que esta pregunta se podría referir a alguna de estas opciones, aunque podría 
    referirse a otra cosa.
    ```   

2) ¿Qué alternativas planteas en el caso que la base de datos relacional de la aplicación se
convierta en un cuello de botella por saturación en las operaciones de lectura? ¿Y para las de
escritura?

   ```
   Para las de lectura habría varias opciones:
   
   - Réplicas de lectura de la base de datos, así las consultas de lectura irían directamente
   a esta/s réplica/s y no impactarían en la base de datos principal.
   
   - Utilizar algún mecanismo de cacheo, con las mismas implicaciones que ya propuse en la pregunta
   anterior.
   
   Para las de escritura se podrían aplicar las dos opciones anteriores ya que así descargarían
   la base de datos principal de las operaciones de lectura. Aparte de estas dos opciones se
   podrían realizar cambios en la arquitectura de la aplicación para implementar CQRS 
   (Command/Query Responsibility Segregation) o Event Sourcing.
   
   Con CQRS desacoplaríamos las operaciones de escritura (Commands) de las de lectura (Queries)
   en dos subsistemas diferenciados, facilitando la optimización de cada uno de los subsistemas
   por separado.
   
   Con Event Sourcing (que es compatible con CQRS) almacenaríamos todas las operaciones en forma
   de eventos en un log de eventos. Con las eventos "a salvo" en el almacén de eventos (es append-only y los eventos
   inmutables), iríamos procesándolos a un ritmo que evitaría las posibles saturaciones que tendríamos si estas 
   operaciones fueran directamente contra la base de datos. Además este procesado sería bastante escalable,
   puesto que podríamos habilitar un determinado número de workers para ello.
   
   En el caso que nos ocupa, veo muy conveniente el uso en especial de Event Sourcing, ya que nos permitiría
   soportar un gran número de transacciones por segundo. Además gracias a la existencia del bus de eventos
   estos siempre estarán ahí guardados, facilitando la posterior resolución de conflictos. En el caso de 
   que fuera contra una base de datos relacional directamente, podrían aflorar problemas de deadlocks, 
   pérdidas o duplicidad de información, caídas de la base de datos...etc.
   
   
   Muchos de estos mecanismos se pueden aplicar a la misma vez.
   ```
   
3) Dicen que las bases de datos relacionales no escalan bien, se me ocurre montar el proyecto
con alguna NoSQL, ¿qué me recomiendas?

   ```
   No creo que sea cierto eso de que las bases de datos relacionales no escalen, es más, diría
   que lo de que un servicio escale es tarea de la arquitectura más que de los componentes en cuestión.
   
   Las NoSQL traen nativamente algunas capacidades que las hacen más aptas que las SQL para aplicar algunos mecanismos
   de escalado horizontal como puede ser el sharding o particionamiento.
   
   Si los datos con los que trabaja el servicio son estructurados, lo que ocurre en la amplia mayoría de casos, veo
   innecesario y hasta contraproducente el uso de una NoSQL como podría ser MongoDB. Por lo que en casi ningún caso
   empezaría un proyecto montándolo sobre NoSQL.
   
   Antes que adoptar una base de datos NoSQL, aplicaría las siguientes soluciones. En caso de que la primera no lo
   solucionara, probaría con la siguiente, y así sucesivamente. 
   
   1) Estudiar y optimizar las queries lentas.
   2) Habría que intentarlo con un escalado vertical de la base de datos, mejorando el hardware de la instancia de esta.
   3) Crear una/s réplica/s de lectura de la base de datos.
   4) Implementar un sistema de caché.
   5) Cluster de base de datos o particionado. La mayoría de las SQL no traen hasta ahora este tipo de soluciones 
   implementadas nativamente, pero existen forks y versiones que sí lo hacen.   
   
   En caso de que ninguna de estas funcionase (o incluso antes de probar con la 5), se debería rehacer la
   arquitectura del proyecto. Implementar CQRS y/o Event Sourcing, se podría dividir en microservicios, o todo a la vez.
   Aunque todo ello conllevaría un aumento de la complejidad del sistema.
   
   Como dije anteriormente, dependiendo de los datos que se manejan en el proyecto, podría tener sentido utilizar
   alguna base de datos NoSQL. Estos serían los casos:
   
   - Si los datos no están muy estructurados y se realizan consultas variadas o búsquedas sobre ellos utilizaría
   MongoDB o ElasticSearch
   - Si los datos tienen baja dimensionalidad y el tiempo es una columna clave, se debería de utilizar una base
   de datos de series de tiempo como pueden ser Influx o Prometheus en otras.
   - Si se necesita realizar análisis sobre datos no normalizadas utilizaría Clickhouse. Clickhouse utiliza
   como lenguaje SQL, aunque digamos que no está diseñado para comportarse igual que las relacionales tradicionales.
   - Si el valor de la información está en la conexión entre los datos o los modelos de las bases de datos relacionales
   usaran relaciones ManyToMany en exceso, usaría alguna base de datos de grafos como Neo4j.
   - Por último, si las estructuras de datos usadas fueran sencillas y variadas, utilizaría Redis.
   
   Esto es un resumen en el que entrarían casi la mayoría de posibles casos de uso. Aparte de estos, 
   puede haber algunos otros casos específicos en los que convendría usar bases de datos no relacionales.
   ```
   
4) ¿Qué tipo de métricas y servicios nos pueden ayudar a comprobar que la API y el servidor
funcionan correctamente?

   ```
   Los servicios que nos podrían ayudar para conocer el estado de nuestro servicio serían los siguientes:
   
   - Servicio de monitorización de sistemas. Como ejemplo, aquí se podría utilizar la dupla Prometheus/Grafana.
   Las métricas que se suelen usar son el uso de CPU, uso de memoria, latencia consultas, latencia de HTTP,
    número de errores HTTP...
   - Servicio de monitorización de logs. Podemos usar el stack ELK (Elastic, Kibana, Logstash) o soluciones integradas
   como Sentry. Configuraríamos métricas y alertas para estar al tanto del número de errores y excepciones de nuestro
   sistema. Estos sistemas también servirían para hacer un seguimiento de los errores.
   - Health checks. Servicios simples que consultarían nuestros sistemas periódicamente para ver que todo sigue como
   se esperaba.
   - Malla de servicios (service mesh). A cada microservicio se le acoplaría un sidecar que aportaría métricas
   estandarizadas y aparte gestionaría problemáticas como el reintento de conexiones, timeouts y
   cortocircuitos. Se puede usar Istio, envoy o linkerd. 
   - Finalmente, podríamos usar un sistema de trazabilidad distribuido, teniendo mayor sentido con el uso de
   microservicios. Estos sistemas nos ayudarían a perfilar y monitorizar nuestras aplicaciones. Nos permiten localizar
   dónde se encuentran los fallos y qué está causando una bajada en el rendimiento. Podemos usar Zipkin o Jaeger para
   ello.
   ```


# API



## Indices

* [businesses](#businesses)

  * [Business signup](#1-business-signup)

* [businesses/transactions](#businessestransactions)

  * [Get business wallet transactions](#1-get-business-wallet-transactions)

* [businesses/wallets](#businesseswallets)

  * [Create business wallet](#1-create-business-wallet)
  * [Debit money to customer wallet](#2-debit-money-to-customer-wallet)
  * [Get business wallet](#3-get-business-wallet)

* [customers](#customers)

  * [Customer signup](#1-customer-signup)

* [customers/transactions](#customerstransactions)

  * [Get all transactions of a customer](#1-get-all-transactions-of-a-customer)
  * [Get all transactions of a customer wallet](#2-get-all-transactions-of-a-customer-wallet)

* [customers/wallets](#customerswallets)

  * [Create customer wallet](#1-create-customer-wallet)
  * [Deposit money in wallet](#2-deposit-money-in-wallet)
  * [Get all wallets of a customer](#3-get-all-wallets-of-a-customer)
  * [Get customer wallet](#4-get-customer-wallet)


--------


## businesses



### 1. Business signup



***Endpoint:***

```bash
Method: POST
Type: RAW
URL: http://{{HOST}}:{{PORT}}/businesses
```



***Body:***

```js        
{
    "name": "Industrias Pepito",
    "email": "pepito@gmail.com",
    "phone": "687137066"
}
```



***More example Requests/Responses:***


##### I. Example Request: Business signup



***Body:***

```js        
{
    "name": "Industrias Pepito",
    "email": "pepitoind@gmail.com",
    "phone": "687137066"
}
```



##### I. Example Response: Business signup
```js
{
    "id": "f50d24ae-4287-427b-a692-f4d440211d49",
    "name": "Industrias Pepito",
    "email": "pepitoind@gmail.com",
    "phone": "687137066",
    "created_at": "2020-08-01T16:32:35.829212",
    "modified_at": "2020-08-01T16:32:35.829212"
}
```


***Status Code:*** 201

<br>



##### II. Example Request: Business signup used email



***Body:***

```js        
{
    "name": "Industrias Pepito",
    "email": "pepito@gmail.com",
    "phone": "687137066"
}
```



##### II. Example Response: Business signup used email
```js
{
    "detail": "That email has already been used to create another account"
}
```


***Status Code:*** 409

<br>



## businesses/transactions



### 1. Get business wallet transactions



***Endpoint:***

```bash
Method: GET
Type: RAW
URL: http://{{HOST}}:{{PORT}}/businesses/wallets/{{business_wallet_id}}/transactions
```



***Body:***

```js        
{
    "business_id": "72c99433-07d6-4cbb-82c5-c26dab148f28"
}
```



***More example Requests/Responses:***


##### I. Example Request: Get business wallet transactions



***Body:***

```js        
{
    "business_id": "72c99433-07d6-4cbb-82c5-c26dab148f28"
}
```



##### I. Example Response: Get business wallet transactions
```js
{
    "transactions": [
        {
            "amount": 40000,
            "description": "Compra coche",
            "status": "denied",
            "created_at": "2020-08-03 12:12:28.356742",
            "error": "The amount debited must be less than the existing balance",
            "id": "59780aff-c201-4eae-9c6d-fd6880326f45",
            "customer_wallet_id": "8036bac9-0231-42d0-8f36-cd2819198e78"
        },
        {
            "amount": 500,
            "description": "Cobro frigorífico",
            "status": "accepted",
            "created_at": "2020-08-03 12:11:07.724301",
            "id": "663f364b-2f12-4b3e-aacb-deb1a33f34ec",
            "customer_wallet_id": "8036bac9-0231-42d0-8f36-cd2819198e78"
        },
        {
            "amount": 500,
            "description": "Cobro tele",
            "status": "accepted",
            "created_at": "2020-08-03 12:09:23.622455",
            "id": "7a7ca37b-f316-4ba7-9fb7-dd44845683ff",
            "customer_wallet_id": "8036bac9-0231-42d0-8f36-cd2819198e78"
        }
    ]
}
```


***Status Code:*** 200

<br>



## businesses/wallets



### 1. Create business wallet



***Endpoint:***

```bash
Method: POST
Type: RAW
URL: http://{{HOST}}:{{PORT}}/businesses/wallets
```



***Body:***

```js        
{
    "business_id": "{{business_id}}"
}
```



***More example Requests/Responses:***


##### I. Example Request: Create business wallet



***Body:***

```js        
{
    "business_id": "72c99433-07d6-4cbb-82c5-c26dab148f28"
}
```



##### I. Example Response: Create business wallet
```js
{
    "id": "fa6c6725-ed55-4fee-b75c-2bcb375b519c",
    "balance": 0,
    "created_at": "2020-08-01T11:35:56.743459",
    "modified_at": "2020-08-01T11:35:56.743459"
}
```


***Status Code:*** 201

<br>



##### II. Example Request: Create business wallet when there is already one



***Body:***

```js        
{
    "business_id": "{{business_id}}"
}
```



##### II. Example Response: Create business wallet when there is already one
```js
{
    "detail": "There can only be one wallet per business"
}
```


***Status Code:*** 409

<br>



##### III. Example Request: Bad business wallet creation without business_id



***Body:***

```js        
{
    "bussiness_id": "72c99433-07d6-4cbb-82c5-c26dab148f28"
}
```



##### III. Example Response: Bad business wallet creation without business_id
```js
{
    "detail": "There is no 'business_id' key in the json of the request"
}
```


***Status Code:*** 400

<br>



### 2. Debit money to customer wallet



***Endpoint:***

```bash
Method: POST
Type: RAW
URL: http://{{HOST}}:{{PORT}}/businesses/wallets/{{business_wallet_id}}/debit
```



***Body:***

```js        
{
    "customer_wallet_id": "{{wallet_id}}",
    "amount": 500,
    "description": "Cobro tele"
}
```



***More example Requests/Responses:***


##### I. Example Request: Debit money to customer wallet



***Body:***

```js        
{
    "customer_wallet_id": "8036bac9-0231-42d0-8f36-cd2819198e78",
    "amount": 500,
    "description": "Cobro frigorífico"
}
```



##### I. Example Response: Debit money to customer wallet
```js
{
    "amount": 500,
    "description": "Cobro frigorífico",
    "id": "663f364b-2f12-4b3e-aacb-deb1a33f34ec"
}
```


***Status Code:*** 201

<br>



##### II. Example Request: Debit money to customer wallet without enough balance



***Body:***

```js        
{
    "customer_wallet_id": "125c8d9d-6de9-4da5-9f84-03edf803ed54",
    "amount": 500,
    "description": "Cobro tele"
}
```



##### II. Example Response: Debit money to customer wallet without enough balance
```js
{
    "detail": "The amount debited must be less than the existing balance"
}
```


***Status Code:*** 409

<br>



### 3. Get business wallet



***Endpoint:***

```bash
Method: GET
Type: RAW
URL: http://{{HOST}}:{{PORT}}/businesses/wallets/{{business_wallet_id}}
```



***Body:***

```js        
{
    "business_id": "72c99433-07d6-4cbb-82c5-c26dab148f28"
}
```



***More example Requests/Responses:***


##### I. Example Request: Get business wallet



***Body:***

```js        
{
    "business_id": "72c99433-07d6-4cbb-82c5-c26dab148f28"
}
```



##### I. Example Response: Get business wallet
```js
{
    "id": "fa6c6725-ed55-4fee-b75c-2bcb375b519c",
    "balance": 0,
    "created_at": "2020-08-01T11:35:56.743459",
    "modified_at": "2020-08-01T11:35:56.743459"
}
```


***Status Code:*** 200

<br>



## customers



### 1. Customer signup



***Endpoint:***

```bash
Method: POST
Type: RAW
URL: http://{{HOST}}:{{PORT}}/customers
```



***Body:***

```js        
{
    "name": "Pablo",
    "last_name": "Guirado",
    "email": "poley@gmail.com",
    "phone": "687137049"
}
```



***More example Requests/Responses:***


##### I. Example Request: Bad Customer signup with used email



***Body:***

```js        
{
    "name": "Pablo",
    "last_name": "Guirado",
    "email": "poley@gmail.com",
    "phone": "687137049"
}
```



##### I. Example Response: Bad Customer signup with used email
```js
{
    "detail": "That email has already been used to create another account"
}
```


***Status Code:*** 409

<br>



##### II. Example Request: Customer signup



***Body:***

```js        
{
    "name": "Pablo",
    "last_name": "Guirado",
    "email": "poley@gmail.com",
    "phone": "687137077"
}
```



##### II. Example Response: Customer signup
```js
{
    "id": "b1c65c3c-d0c7-4b94-89ba-40e0f9604b2e",
    "name": "Pablo",
    "last_name": "Guirado",
    "email": "poley@gmail.com",
    "phone": "687137077"
}
```


***Status Code:*** 201

<br>



## customers/transactions



### 1. Get all transactions of a customer



***Endpoint:***

```bash
Method: GET
Type: 
URL: http://{{HOST}}:{{PORT}}/customers/{{customer_id}}/transactions
```



***More example Requests/Responses:***


##### I. Example Request: Get all transactions of a customer (different transactions)



##### I. Example Response: Get all transactions of a customer (different transactions)
```js
{
    "wallets": [
        {
            "id": "8036bac9-0231-42d0-8f36-cd2819198e78",
            "transactions": [
                {
                    "amount": 40000,
                    "description": "Compra coche",
                    "status": "denied",
                    "created_at": "2020-08-03 12:12:28.356742",
                    "error": "The amount debited must be less than the existing balance",
                    "id": "59780aff-c201-4eae-9c6d-fd6880326f45",
                    "business_wallet_id": "a2ca7425-d60c-4267-ac04-7876e0a85898"
                },
                {
                    "amount": 500,
                    "description": "Cobro frigorífico",
                    "status": "accepted",
                    "created_at": "2020-08-03 12:11:07.724301",
                    "id": "663f364b-2f12-4b3e-aacb-deb1a33f34ec",
                    "business_wallet_id": "a2ca7425-d60c-4267-ac04-7876e0a85898"
                },
                {
                    "amount": 500,
                    "description": "Cobro tele",
                    "status": "accepted",
                    "created_at": "2020-08-03 12:09:23.622455",
                    "id": "7a7ca37b-f316-4ba7-9fb7-dd44845683ff",
                    "business_wallet_id": "a2ca7425-d60c-4267-ac04-7876e0a85898"
                },
                {
                    "amount": 500,
                    "description": "Apertura cuenta",
                    "status": "accepted",
                    "created_at": "2020-08-03 11:57:21.235160",
                    "id": "2795df0d-6e3e-4bc3-87b5-670ba1eb804f"
                },
                {
                    "amount": 500,
                    "description": "Apertura cuenta",
                    "status": "accepted",
                    "created_at": "2020-08-03 11:52:50.473025",
                    "id": "bf6bb376-7e12-43b9-999c-ad1ab489fd8e"
                }
            ]
        }
    ]
}
```


***Status Code:*** 200

<br>



##### II. Example Request: Get all transactions of a customer



##### II. Example Response: Get all transactions of a customer
```js
{
    "wallets": [
        {
            "id": "8036bac9-0231-42d0-8f36-cd2819198e78",
            "transactions": [
                {
                    "amount": 500,
                    "description": "Apertura cuenta",
                    "status": "accepted",
                    "created_at": "2020-08-03 11:57:21.235160",
                    "id": "2795df0d-6e3e-4bc3-87b5-670ba1eb804f"
                },
                {
                    "amount": 500,
                    "description": "Apertura cuenta",
                    "status": "accepted",
                    "created_at": "2020-08-03 11:52:50.473025",
                    "id": "bf6bb376-7e12-43b9-999c-ad1ab489fd8e"
                }
            ]
        }
    ]
}
```


***Status Code:*** 200

<br>



### 2. Get all transactions of a customer wallet



***Endpoint:***

```bash
Method: GET
Type: 
URL: http://{{HOST}}:{{PORT}}/customers/wallets/{{wallet_id}}/transactions
```



***More example Requests/Responses:***


##### I. Example Request: Get all transactions of a customer wallet (different transactions)



##### I. Example Response: Get all transactions of a customer wallet (different transactions)
```js
{
    "transactions": [
        {
            "amount": 500,
            "description": "Apertura cuenta",
            "status": "accepted",
            "created_at": "2020-08-01 19:42:45.164079"
        },
        {
            "amount": 500,
            "description": "Apertura cuenta",
            "status": "accepted",
            "created_at": "2020-08-01 19:41:18.787873"
        },
        {
            "amount": 500,
            "description": "Cobro tele",
            "status": "denied",
            "created_at": "2020-08-01 19:33:36.386949",
            "error": "The amount debited must be less than the existing balance",
            "business_wallet_id": "27c76390-8488-4d27-8173-de6447c7e7f5"
        }
    ]
}
```


***Status Code:*** 200

<br>



##### II. Example Request: Get all transactions of a customer wallet



##### II. Example Response: Get all transactions of a customer wallet
```js
{
    "transactions": [
        {
            "amount": 500,
            "description": "Apertura cuenta",
            "status": "accepted",
            "created_at": "2020-08-03 11:57:21.235160",
            "id": "2795df0d-6e3e-4bc3-87b5-670ba1eb804f"
        },
        {
            "amount": 500,
            "description": "Apertura cuenta",
            "status": "accepted",
            "created_at": "2020-08-03 11:52:50.473025",
            "id": "bf6bb376-7e12-43b9-999c-ad1ab489fd8e"
        }
    ]
}
```


***Status Code:*** 200

<br>



## customers/wallets



### 1. Create customer wallet



***Endpoint:***

```bash
Method: POST
Type: RAW
URL: http://{{HOST}}:{{PORT}}/customers/wallets
```



***Body:***

```js        
{
    "customer_id": "{{customer_id}}"
}
```



***More example Requests/Responses:***


##### I. Example Request: Create customer wallet



***Body:***

```js        
{
    "customer_id": "ae991d93-a6b7-4906-a850-9752430dac12"
}
```



##### I. Example Response: Create customer wallet
```js
{
    "id": "36f1cfba-e466-450a-b84a-07d45fa79c5b",
    "balance": 0
}
```


***Status Code:*** 200

<br>



##### II. Example Request: Bad Customer Wallet creation without customer_id



***Body:***

```js        
{
    "name": "Pablo",
    "last_name": "Guirado",
    "email": "poley@gmail.com",
    "phone": "687137077"
}
```



##### II. Example Response: Bad Customer Wallet creation without customer_id
```js
{
    "detail": "There is no 'customer_id' key in the json of the request"
}
```


***Status Code:*** 400

<br>



### 2. Deposit money in wallet



***Endpoint:***

```bash
Method: POST
Type: RAW
URL: http://{{HOST}}:{{PORT}}/customers/wallets/{{wallet_id}}/deposit
```



***Body:***

```js        
{
    "amount": 500,
    "description": "Apertura cuenta"
}
```



***More example Requests/Responses:***


##### I. Example Request: Deposit money in wallet with negative amount



***Body:***

```js        
{
    "amount": -500,
    "description": "Apertura cuenta"
}
```



##### I. Example Response: Deposit money in wallet with negative amount
```js
{
    "detail": "The entered amount must be a positive number"
}
```


***Status Code:*** 400

<br>



##### II. Example Request: Deposit money in wallet



***Body:***

```js        
{
    "amount": 500,
    "description": "Apertura cuenta"
}
```



##### II. Example Response: Deposit money in wallet
```js
{
    "amount": 500,
    "description": "Apertura cuenta",
    "id": "2795df0d-6e3e-4bc3-87b5-670ba1eb804f"
}
```


***Status Code:*** 201

<br>



### 3. Get all wallets of a customer



***Endpoint:***

```bash
Method: GET
Type: 
URL: http://{{HOST}}:{{PORT}}/customers/{{customer_id}}/wallets
```



***More example Requests/Responses:***


##### I. Example Request: Get all wallets of a customer



##### I. Example Response: Get all wallets of a customer
```js
{
    "wallets": [
        {
            "id": "80c0683a-8f7d-46d3-b0a0-baf6c7f6e89e",
            "balance": 0,
            "created_at": "2020-07-31T19:53:11.790613",
            "modified_at": "2020-07-31T19:53:11.790613"
        }
    ]
}
```


***Status Code:*** 200

<br>



### 4. Get customer wallet



***Endpoint:***

```bash
Method: GET
Type: 
URL: http://{{HOST}}:{{PORT}}/customers/wallets/{{wallet_id}}
```



***More example Requests/Responses:***


##### I. Example Request: Get customer wallet



##### I. Example Response: Get customer wallet
```js
{
    "id": "0036625c-defc-44b3-8c15-da7bfb78c7cf",
    "balance": 0
}
```


***Status Code:*** 200

<br>



##### II. Example Request: Get customer wallet with bad id



##### II. Example Response: Get customer wallet with bad id
```js
{
    "detail": "There is no wallet with id 36f1cfba-e466-450a-b84a-07d45fa79c5b"
}
```


***Status Code:*** 404

<br>

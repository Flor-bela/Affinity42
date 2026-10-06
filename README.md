# Affinity42

// to do:
añadir horas
traducir a inglés
decir los requirements que tenemos que instalar
añadir streamlit run app.py
y otros requisitos necesarios para el readme!!!



logins: durisosa dstanimi luolivei fda-roch

Affinity42: estudiantes que sean más “afines” a nosotros; -> calcular y visualizar un Índice de Afinidad para identificar estudiantes con perfiles y ritmos de trabajo parecidos. El objetivo es encontrar compañeros compatibles para futuros proyectos en grupo basándonos en los proyectos completados y en cuando fueron terminados (para asegurar que los conocimientos estén "frescos"). 

Frontend: Dobrin; Streamlit

Powerpoint/presentación y Frontend: Lucas

Backend/Data: Flor y Durian
Tener en cuenta: fechas de término de proyectos; fecha de inscripción en los proyectos y ver qué más se puede usar para calcular el índice (índice de Jaccard -> para medir la intersección de proyectos completados entre estudiantes).


—----------------------------------------------------------------------------------------------------------------
índice de afinidad - cómo se calcula:
Índice de jaccard: 
Nº de proyectos en común (intersección) / Nº total de proyectos únicos entre las dos personas que comparamos -> unión)

// añadir esta imagen 
https://storage.googleapis.com/lds-media/images/jaccard_similarity.width-1200.jpg


“Bonus time”:
Si hemos terminado los proyectos en menos de 30 días (<= 30) de diferencia, sumamos 0.05 al índice.

Índice de afinidad final: (índice de jaccard + “bonus time”) * 100 (para transformarlo en porcentaje)

-> Nota: el índice de afinidad hace tope en 100% (independientemente de cuantos “bonus time” hemos añadido)

—----------------------------------------------------------------------------------------------------------------


Hacer:
-> ver cómo representar el índice de afinidad “gráficamente”; qué datos usar para calcularla o no; 
-> Filtrar datos por estudiantes en el cluster; grade: cadet (para filtrar solamente los estudiantes y no los piscineros); (Campus Madrid: código 22; Solo proyectos del cursus (sin los de Piscina: código 21)
-> Generar matriz de afinidad y ver cómo podemos ir actualizando con la API (cuantos requests, cuánto tiempo necesitamos….etc)


Enlaces útiles:
https://profile.intra.42.fr/legal/terms/33
https://api.intra.42.fr/apidoc/guides/getting_started
https://api.intra.42.fr/apidoc/guides/web_application_flow



-----
Project for Hackathon 42442 (Liga Nexus)

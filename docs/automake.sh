while inotifywait -qre modify source/; do
    make html
done

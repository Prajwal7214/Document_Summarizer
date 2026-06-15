import FileUpload from '../components/FileUpload';

const Home = () => {
  return (
    <div className="h-full flex flex-col items-center justify-center max-w-3xl mx-auto space-y-8 py-8">
      <div className="space-y-4 text-center">
        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
          Summarix
        </h1>
        <p className="text-gray-500 text-lg">
          Upload your documents and let AI generate concise, accurate summaries in seconds.
        </p>
      </div>

      <div className="w-full mt-4">
        <FileUpload />
      </div>
    </div>
  );
};

export default Home;
